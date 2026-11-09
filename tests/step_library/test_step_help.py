# coding: utf-8
"""画布 Step 帮助功能测试：
1. 悬停 Step 问号图标显示说明 Tooltip；
2. 选中 Step 按 F1 打开外部浏览器帮助页面。
"""

import time

import pytest
import win32gui  # pyright: ignore[reportMissingModuleSource]
from pywinauto import Application, keyboard

from pages.main_window_page import MainWindowPage
from tests.step_library.test_create_steps import STEP_NAME, clear_canvas_steps
from utils.image_locator import (
    TEMPLATE_DIR,
    click_match,
    hover_match,
    locate_step_help_icon,
    locate_template,
    visible_tooltip_handles,
    wait_for_visible_tooltip,
)


STEP_TITLE_TEMPLATE = TEMPLATE_DIR / "ai_classify_title.png"
HELP_ICON_TEMPLATE = TEMPLATE_DIR / "step_help_icon.png"
BROWSER_WINDOW_CLASSES = {
    "Chrome_WidgetWin_1",  # Chrome、Edge
    "MozillaWindowClass",  # Firefox
}
EXPECTED_HELP_URL = "https://docs.mech-mind.net/zh/home/latest/index.html"


def browser_url(hwnd: int) -> str:
    """通过 UIA 读取浏览器地址栏 URL。"""
    browser = Application(backend="uia").connect(handle=hwnd)
    window = browser.window(handle=hwnd)
    for edit in window.descendants(control_type="Edit"):
        value = edit.get_value().strip()
        if "docs.mech-mind.net/" in value:
            if not value.startswith(("http://", "https://")):
                value = f"https://{value}"
            return value
    return ""


def wait_for_browser(
    expected_url: str = EXPECTED_HELP_URL,
    timeout: float = 15,
) -> tuple[int, str, str]:
    """等待外部浏览器打开指定的帮助文档 URL。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        hwnd = win32gui.GetForegroundWindow()
        if (
            hwnd
            and win32gui.IsWindowVisible(hwnd)
            and win32gui.GetClassName(hwnd) in BROWSER_WINDOW_CLASSES
        ):
            url = browser_url(hwnd)
            if url == expected_url:
                return hwnd, win32gui.GetWindowText(hwnd), url
        time.sleep(0.2)
    raise TimeoutError(f"{timeout} 秒内没有打开帮助页面：{expected_url}")


@pytest.fixture(scope="module", autouse=True)
def prepare_single_step_on_canvas(main_page: MainWindowPage):
    """模块前置：使用最外层 conftest 的 main_page 拖入 1 个 Step 供两条帮助测试复用。"""
    clear_canvas_steps(main_page)
    step_item = main_page.step_library.locate(STEP_NAME)
    destination = main_page.project_editor.canvas_point(0.55, 0.35)
    main_page.step_library.drag_item_to(step_item, destination)
    print(f"帮助测试已准备 Step：{STEP_NAME}，画布坐标 {destination}")
    yield
    clear_canvas_steps(main_page)


def test_01_step_help_tooltip(main_page: MainWindowPage) -> None:
    """用例1：悬停 Step 问号图标，验证说明 Tooltip 可见且已渲染内容。"""
    main_page.focus()
    title_match, help_match, _screenshot, _origin = locate_step_help_icon(
        STEP_TITLE_TEMPLATE,
        HELP_ICON_TEMPLATE,
        threshold=0.8,
        help_threshold=0.65,
        timeout=15,
        hwnd=main_page.handle,
        scales=(0.75, 0.9, 1.0, 1.1, 1.25, 1.5),
    )
    print(
        f"问号定位成功：标题相似度 {title_match.score:.3f}，"
        f"问号相似度 {help_match.score:.3f}"
    )

    existing_tooltips = visible_tooltip_handles(main_page.handle)
    hover_match(help_match, seconds=0.5)
    tooltip_text = wait_for_visible_tooltip(
        timeout=5,
        ignored_handles=existing_tooltips,
        main_hwnd=main_page.handle,
    )

    print(f"Step 说明：{tooltip_text}")
    assert tooltip_text.strip(), "悬停问号后未显示 Step 说明"


def test_02_step_f1_opens_help_page(main_page: MainWindowPage) -> None:
    """用例2：点击选中同一个 Step 后按 F1，验证外部浏览器打开帮助页面。"""
    main_page.focus()
    title_match, _screenshot, _origin = locate_template(
        STEP_TITLE_TEMPLATE,
        threshold=0.8,
        timeout=15,
        hwnd=main_page.handle,
        scales=(0.75, 0.9, 1.0, 1.1, 1.25, 1.5),
    )
    click_match(title_match, offset=(0.25, 0.5))
    time.sleep(0.3)

    keyboard.send_keys("{F1}")
    browser_handle, browser_title, browser_url_value = wait_for_browser()

    print(
        f"F1 帮助页面打开成功：handle={browser_handle}，"
        f"title={browser_title!r}，url={browser_url_value!r}"
    )
    assert browser_url_value == EXPECTED_HELP_URL
