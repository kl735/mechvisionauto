# coding: utf-8
"""通过截图模板匹配定位 Mech-Vision 界面元素。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import ctypes
import time

import cv2
import numpy as np
import win32con  # pyright: ignore[reportMissingModuleSource]
import win32gui  # pyright: ignore[reportMissingModuleSource]
import win32ui  # pyright: ignore[reportMissingModuleSource]
from PIL import Image, ImageDraw, ImageFont, ImageGrab
from pywinauto import keyboard, mouse


WINDOW_TITLE = "Mech-Vision"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
DEFAULT_THRESHOLD = 0.8
TEXT_MATCH_THRESHOLD = 0.55
LOCATE_TIMEOUT = 15
TEXT_FONT = Path(r"C:\Windows\Fonts\msyh.ttc")
TEXT_FONT_SIZES = (12, 13, 14, 15, 16, 18, 20)


@dataclass(frozen=True)
class ImageMatch:
    """截图匹配结果，坐标均为屏幕像素。"""

    left: int
    top: int
    width: int
    height: int
    score: float

    @property
    def center(self) -> tuple[int, int]:
        return (self.left + self.width // 2, self.top + self.height // 2)

    @property
    def box(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.width, self.height)


def _ensure_dpi_aware() -> None:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def find_mech_vision_hwnd() -> int:
    """查找 Mech-Vision 主窗口句柄。最小化时先还原。"""
    handles: list[int] = []

    def callback(hwnd: int, _: object) -> bool:
        title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        if WINDOW_TITLE in title and "QWindowPopup" not in class_name:
            handles.append(hwnd)
        return True

    win32gui.EnumWindows(callback, None)
    if not handles:
        raise RuntimeError("未找到 Mech-Vision 主窗口")

    main = None
    for hwnd in handles:
        if win32gui.GetClassName(hwnd) == "Qt5152QWindowIcon":
            main = hwnd
            break
    hwnd = main or handles[0]
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(1.0)
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    if right - left < 800 or bottom - top < 500:
        raise RuntimeError(
            f"Mech-Vision 窗口过小，无法截图定位：{(right - left, bottom - top)}"
        )
    return hwnd


def capture_window(hwnd: int) -> tuple[Image.Image, tuple[int, int]]:
    """截取窗口客户图像，并返回图像及窗口左上角屏幕坐标。"""
    _ensure_dpi_aware()
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top
    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
    save_dc.SelectObject(bitmap)
    save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
    info = bitmap.GetInfo()
    bits = bitmap.GetBitmapBits(True)
    image = Image.frombuffer(
        "RGB",
        (info["bmWidth"], info["bmHeight"]),
        bits,
        "raw",
        "BGRX",
        0,
        1,
    )
    win32gui.DeleteObject(bitmap.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)
    return image, (left, top)


def _to_bgr(image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)


def _read_template(template_path: Path) -> np.ndarray:
    image = Image.open(template_path).convert("RGB")
    return _to_bgr(image)


def match_on_image(
    screenshot: Image.Image,
    origin: tuple[int, int],
    template_path: str | Path,
    region: tuple[int, int, int, int] | None = None,
    threshold: float = DEFAULT_THRESHOLD,
    scales: tuple[float, ...] = (1.0, 0.9, 1.1),
) -> ImageMatch:
    """在已截取的窗口图上匹配模板。region 为屏幕坐标 (left, top, width, height)。"""
    template = _read_template(Path(template_path))
    screen = _to_bgr(screenshot)
    offset_x = 0
    offset_y = 0
    if region is not None:
        local_left = max(0, region[0] - origin[0])
        local_top = max(0, region[1] - origin[1])
        local_right = min(screen.shape[1], local_left + region[2])
        local_bottom = min(screen.shape[0], local_top + region[3])
        screen = screen[local_top:local_bottom, local_left:local_right]
        offset_x = local_left
        offset_y = local_top
        if screen.size == 0:
            raise TimeoutError("指定区域内没有可匹配的图像")

    best: ImageMatch | None = None
    for scale in scales:
        sized = cv2.resize(
            template,
            (
                max(1, int(template.shape[1] * scale)),
                max(1, int(template.shape[0] * scale)),
            ),
            interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR,
        )
        if sized.shape[0] > screen.shape[0] or sized.shape[1] > screen.shape[1]:
            continue
        result = cv2.matchTemplate(screen, sized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        match = ImageMatch(
            left=origin[0] + offset_x + int(max_loc[0]),
            top=origin[1] + offset_y + int(max_loc[1]),
            width=int(sized.shape[1]),
            height=int(sized.shape[0]),
            score=float(max_val),
        )
        if best is None or match.score > best.score:
            best = match
        if match.score >= threshold:
            return match

    score = best.score if best else 0.0
    raise TimeoutError(
        f"未在指定区域找到模板 {Path(template_path).name}，"
        f"最高相似度 {score:.3f}，阈值 {threshold}"
    )


def locate_step_help_icon(
    step_title_template: str | Path,
    help_icon_template: str | Path,
    threshold: float = DEFAULT_THRESHOLD,
    timeout: float = LOCATE_TIMEOUT,
) -> tuple[ImageMatch, ImageMatch, Image.Image, tuple[int, int]]:
    """先定位 Step 标题，再在标题右侧查找问号帮助图标。"""
    title_match, screenshot, origin = locate_template(
        step_title_template,
        threshold=threshold,
        timeout=timeout,
    )
    help_region = (
        title_match.left + title_match.width - 8,
        title_match.top - 12,
        72,
        title_match.height + 24,
    )
    help_match = match_on_image(
        screenshot,
        origin,
        help_icon_template,
        region=help_region,
        threshold=threshold,
    )
    return title_match, help_match, screenshot, origin


def locate_step_config_wizard(
    step_title_template: str | Path,
    wizard_template: str | Path,
    threshold: float = DEFAULT_THRESHOLD,
    timeout: float = LOCATE_TIMEOUT,
) -> tuple[ImageMatch, ImageMatch, Image.Image, tuple[int, int]]:
    """先定位 Step 标题，再在标题右侧查找配置向导。"""
    title_match, screenshot, origin = locate_template(
        step_title_template,
        threshold=threshold,
        timeout=timeout,
    )
    wizard_region = (
        title_match.left + title_match.width - 20,
        title_match.top - 24,
        420,
        title_match.height + 40,
    )
    wizard_match = match_on_image(
        screenshot,
        origin,
        wizard_template,
        region=wizard_region,
        threshold=threshold,
    )
    return title_match, wizard_match, screenshot, origin


def _render_text(text: str, font_size: int) -> np.ndarray:
    """把当前标题文字画成灰度图，避免依赖以前保存的模板截图。"""
    font = ImageFont.truetype(str(TEXT_FONT), font_size)
    probe = ImageDraw.Draw(Image.new("L", (1, 1)))
    left, top, right, bottom = probe.textbbox((0, 0), text, font=font)
    image = Image.new("L", (right - left + 4, bottom - top + 4), 0)
    ImageDraw.Draw(image).text((2 - left, 2 - top), text, font=font, fill=255)
    return np.array(image)


def locate_text(
    text: str,
    region: tuple[int, int, int, int] | None = None,
    threshold: float = TEXT_MATCH_THRESHOLD,
    timeout: float = LOCATE_TIMEOUT,
) -> tuple[ImageMatch, Image.Image, tuple[int, int]]:
    """在当前窗口截图中定位文字。region 为屏幕坐标 (left, top, width, height)。"""
    if not TEXT_FONT.is_file():
        raise FileNotFoundError(f"未找到用于绘制标题的字体：{TEXT_FONT}")

    _ensure_dpi_aware()
    hwnd = find_mech_vision_hwnd()
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    templates = [_render_text(text, size) for size in TEXT_FONT_SIZES]
    deadline = time.monotonic() + timeout
    best: tuple[float, ImageMatch, Image.Image, tuple[int, int]] | None = None

    while time.monotonic() < deadline:
        screenshot, origin = capture_window(hwnd)
        gray = cv2.cvtColor(_to_bgr(screenshot), cv2.COLOR_BGR2GRAY)
        search_left = 0
        search_top = 0
        search_image = gray
        if region is not None:
            search_left = max(0, region[0] - origin[0])
            search_top = max(0, region[1] - origin[1])
            search_right = min(gray.shape[1], search_left + region[2])
            search_bottom = min(gray.shape[0], search_top + region[3])
            search_image = gray[search_top:search_bottom, search_left:search_right]
        for template in templates:
            if (
                template.shape[0] > search_image.shape[0]
                or template.shape[1] > search_image.shape[1]
            ):
                continue
            result = cv2.matchTemplate(search_image, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            match = ImageMatch(
                left=origin[0] + search_left + int(max_loc[0]),
                top=origin[1] + search_top + int(max_loc[1]),
                width=int(template.shape[1]),
                height=int(template.shape[0]),
                score=float(max_val),
            )
            if best is None or match.score > best[0]:
                best = (match.score, match, screenshot, origin)
            if match.score >= threshold:
                return match, screenshot, origin
        time.sleep(0.4)

    score = best[0] if best else 0.0
    raise TimeoutError(
        f"{timeout} 秒内未在当前截图中找到文字 {text!r}，"
        f"最高相似度 {score:.3f}，阈值 {threshold}"
    )


def locate_template(
    template_path: str | Path,
    threshold: float = DEFAULT_THRESHOLD,
    timeout: float = LOCATE_TIMEOUT,
    scales: tuple[float, ...] = (1.0, 0.9, 1.1),
    region: tuple[int, int, int, int] | None = None,
) -> tuple[ImageMatch, Image.Image, tuple[int, int]]:
    """在 Mech-Vision 窗口中定位模板图，超时则抛出异常。"""
    _ensure_dpi_aware()
    template_file = Path(template_path)
    if not template_file.is_file():
        raise FileNotFoundError(f"未找到模板图：{template_file}")

    template = _read_template(template_file)
    hwnd = find_mech_vision_hwnd()
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    deadline = time.monotonic() + timeout
    best: tuple[float, ImageMatch, Image.Image, tuple[int, int]] | None = None

    while time.monotonic() < deadline:
        screenshot, origin = capture_window(hwnd)
        screen = _to_bgr(screenshot)
        search_left = 0
        search_top = 0
        search_image = screen
        if region is not None:
            search_left = max(0, region[0] - origin[0])
            search_top = max(0, region[1] - origin[1])
            search_right = min(screen.shape[1], search_left + region[2])
            search_bottom = min(screen.shape[0], search_top + region[3])
            search_image = screen[search_top:search_bottom, search_left:search_right]
        for scale in scales:
            sized = cv2.resize(
                template,
                (
                    max(1, int(template.shape[1] * scale)),
                    max(1, int(template.shape[0] * scale)),
                ),
                interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR,
            )
            if (
                sized.shape[0] > search_image.shape[0]
                or sized.shape[1] > search_image.shape[1]
            ):
                continue
            result = cv2.matchTemplate(search_image, sized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            match = ImageMatch(
                left=origin[0] + search_left + int(max_loc[0]),
                top=origin[1] + search_top + int(max_loc[1]),
                width=int(sized.shape[1]),
                height=int(sized.shape[0]),
                score=float(max_val),
            )
            if best is None or match.score > best[0]:
                best = (match.score, match, screenshot, origin)
            if match.score >= threshold:
                return match, screenshot, origin
        time.sleep(0.4)

    score = best[0] if best else 0.0
    raise TimeoutError(
        f"{timeout} 秒内未在屏幕上找到模板 {template_file.name}，"
        f"最高相似度 {score:.3f}，阈值 {threshold}"
    )


def save_match_preview(
    match: ImageMatch,
    screenshot: Image.Image,
    origin: tuple[int, int],
    output_path: str | Path,
) -> None:
    """把匹配框画在定位用的同一张截图上。"""
    canvas = _to_bgr(screenshot)
    local_left = match.left - origin[0]
    local_top = match.top - origin[1]
    cv2.rectangle(
        canvas,
        (local_left, local_top),
        (local_left + match.width, local_top + match.height),
        (0, 0, 255),
        3,
    )
    center = (
        local_left + match.width // 2,
        local_top + match.height // 2,
    )
    cv2.drawMarker(canvas, center, (0, 255, 0), cv2.MARKER_CROSS, 24, 2)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).save(output)


def move_to_match(match: ImageMatch) -> None:
    """把鼠标移到匹配中心，用于人工确认定位。"""
    mouse.move(coords=match.center)


def hover_match(match: ImageMatch, seconds: float = 2.0) -> None:
    """鼠标悬停在匹配中心指定秒数，用于弹出问号提示。"""
    mouse.move(coords=match.center)
    time.sleep(seconds)


def grab_full_screen(output_path: str | Path) -> Path:
    """截取整屏（含独立弹出的 Tooltip 窗口）。"""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    ImageGrab.grab(all_screens=True).save(output)
    return output


def click_match(match: ImageMatch, offset: tuple[float, float] = (0.5, 0.5)) -> None:
    """点击匹配区域，默认中心；offset 为宽高比例，避免点到问号。"""
    point = (
        match.left + int(match.width * offset[0]),
        match.top + int(match.height * offset[1]),
    )
    mouse.click(button="left", coords=point)


def press_delete() -> None:
    """先激活 Mech-Vision，再发送 Delete。"""
    hwnd = find_mech_vision_hwnd()
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    time.sleep(0.2)
    keyboard.send_keys("{DELETE}")
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_DELETE, 0)
    time.sleep(0.05)
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_DELETE, 0)
