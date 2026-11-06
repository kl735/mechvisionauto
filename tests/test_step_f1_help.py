# coding: utf-8
"""验证选中画布 Step 后按 F1 能打开外部帮助页面。"""

import time

import win32con  # pyright: ignore[reportMissingModuleSource]
import win32gui  # pyright: ignore[reportMissingModuleSource]
from pywinauto import Application, keyboard

from utils.image_locator import TEMPLATE_DIR, click_match, locate_template
from pages.main_window_page import MainWindowPage


STEP_NAME = "AI分类（正反/有无）"
STEP_TITLE_TEMPLATE = TEMPLATE_DIR / "ai_classify_title.png"
BROWSER_WINDOW_CLASSES = {
    "Chrome_WidgetWin_1",  # Chrome、Edge
    "MozillaWindowClass",  # Firefox
}
EXPECTED_HELP_URL = "https://docs.mech-mind.net/zh/home/latest/index.html"


# def prepare_main_window(main_page: MainWindowPage) -> None:
#     """把窗口移到主显示器，保证鼠标与截图使用同一套坐标。"""
#     win32gui.ShowWindow(main_page.handle, win32con.SW_RESTORE)
#     win32gui.SetWindowPos(
#         main_page.handle,
#         win32con.HWND_TOP,
#         0,
#         0,
#         1200,
#         800,
#         win32con.SWP_SHOWWINDOW,
#     )
#     win32gui.ShowWindow(main_page.handle, win32con.SW_MAXIMIZE)
#     time.sleep(0.8)


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


def wait_for_browser(timeout: float = 15) -> tuple[int, str, str]:
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
            if url == EXPECTED_HELP_URL:
                return hwnd, win32gui.GetWindowText(hwnd), url
        time.sleep(0.2)
    raise TimeoutError(
        f"{timeout} 秒内没有打开帮助页面：{EXPECTED_HELP_URL}"
    )


def test_selected_step_f1_opens_help_page(main_page: MainWindowPage) -> None:
    """创建并选中 Step，按 F1 后验证外部帮助页面已打开。"""
    # prepare_main_window(main_page)
    step_library = main_page.step_library
    step = step_library.locate(STEP_NAME)

    main_page.focus()
    destination = main_page.project_editor.canvas_point(0.55, 0.35)
    step_library.drag_item_to(step, destination)

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
