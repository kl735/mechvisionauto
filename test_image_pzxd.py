# coding: utf-8
"""截图定位 AI 分类步骤上的配置向导。"""

from pathlib import Path
import ctypes
import time

from PIL import ImageGrab
import win32con  # pyright: ignore[reportMissingModuleSource]
import win32gui  # pyright: ignore[reportMissingModuleSource]

from image_locator import (
    TEMPLATE_DIR,
    find_mech_vision_hwnd,
    locate_step_config_wizard,
    save_match_preview,
)


STEP_TITLE_TEMPLATE = TEMPLATE_DIR / "ai_classify_title.png"
WIZARD_TEMPLATE = TEMPLATE_DIR / "config_wizard.png"
PREVIEW_PATH = TEMPLATE_DIR / "locate_config_wizard.png"
PAGE_SHOT_PATH = TEMPLATE_DIR / "config_wizard_page.png"


def grab_mech_vision_screen(output_path: Path) -> Path:
    """按窗口矩形截屏，能拍到叠在主窗口上的新页面。"""
    hwnd = find_mech_vision_hwnd()
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    image = ImageGrab.grab(
        bbox=(left, top, right, bottom),
        all_screens=True,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path


def maximize_mech_vision() -> None:
    """最大化 Mech-Vision，避免窗口尺寸变化导致模板匹配失败。"""
    hwnd = find_mech_vision_hwnd()
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
    time.sleep(0.8)


def test_locate_config_wizard() -> None:
    """定位 AI分类（正反/有无）标题右侧的配置向导。"""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()

    print(f"步骤标题模板：{STEP_TITLE_TEMPLATE}")
    print(f"配置向导模板：{WIZARD_TEMPLATE}")

    maximize_mech_vision()

    # 先定位步骤标题，再在标题右侧匹配配置向导
    title_match, wizard_match, screenshot, origin = locate_step_config_wizard(
        STEP_TITLE_TEMPLATE,
        WIZARD_TEMPLATE,
        threshold=0.8,
        timeout=15,
    )
    save_match_preview(wizard_match, screenshot, origin, PREVIEW_PATH)

    print("配置向导定位成功")
    print(f"标题相似度：{title_match.score:.3f}  中心：{title_match.center}")
    print(f"配置向导相似度：{wizard_match.score:.3f}  中心：{wizard_match.center}")
    print(f"配置向导屏幕坐标：{wizard_match.box}")
    print(f"预览图：{PREVIEW_PATH}")

    # 点击配置向导中心。旧模板偏高，点在卡片上只会选中 Step
    hwnd = find_mech_vision_hwnd()
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass
    time.sleep(0.3)
    click_x, click_y = wizard_match.center
    ctypes.windll.user32.SetCursorPos(click_x, click_y)
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(2.0)
    print(f"已点击：配置向导 ({click_x}, {click_y})")

    # 截取进入后的新页面
    grab_mech_vision_screen(PAGE_SHOT_PATH)
    print(f"新页面截图：{PAGE_SHOT_PATH}")


if __name__ == "__main__":
    test_locate_config_wizard()
