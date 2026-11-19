# coding: utf-8
"""外部浏览器窗口查询与文档 URL 等待。"""

from __future__ import annotations

import time
from urllib.parse import urlparse, urlunparse

import win32gui  # pyright: ignore[reportMissingModuleSource]
from pywinauto import Application


BROWSER_WINDOW_CLASSES = {
    "Chrome_WidgetWin_1",  # Chrome、Edge
    "MozillaWindowClass",  # Firefox
}
DOCS_HOST = "docs.mech-mind.net"


def visible_browser_windows() -> list[int]:
    """返回当前可见的浏览器顶层窗口句柄。"""
    handles: list[int] = []

    def collect(hwnd: int, _: object) -> bool:
        if (
            win32gui.IsWindowVisible(hwnd)
            and win32gui.GetClassName(hwnd) in BROWSER_WINDOW_CLASSES
        ):
            handles.append(hwnd)
        return True

    win32gui.EnumWindows(collect, None)
    return handles


def browser_url(hwnd: int, host: str | None = None) -> str:
    """通过 UIA 读取浏览器地址栏中匹配指定站点的 URL。"""
    expected_host = (host or DOCS_HOST).lower()
    try:
        browser = Application(backend="uia").connect(handle=hwnd)
        window = browser.window(handle=hwnd)
        for edit in window.descendants(control_type="Edit"):
            try:
                value = (edit.get_value() or "").strip()
            except Exception:
                continue
            if expected_host not in value.lower():
                continue
            if not value.startswith(("http://", "https://")):
                value = f"https://{value}"
            return value
    except Exception:
        return ""
    return ""


def normalize_docs_url(url: str) -> str:
    """去掉 query、fragment 和末尾斜杠，统一为 https host+path。"""
    text = (url or "").strip()
    if not text:
        return ""
    if not text.startswith(("http://", "https://")):
        text = f"https://{text}"
    parsed = urlparse(text)
    path = parsed.path.rstrip("/")
    return urlunparse(("https", parsed.netloc.lower(), path, "", "", ""))


def urls_match(actual: str, expected: str) -> bool:
    """判断实际 URL 是否与期望文档地址指向同一页面。"""
    actual_norm = normalize_docs_url(actual)
    expected_norm = normalize_docs_url(expected)
    if not actual_norm or not expected_norm:
        return False
    if actual_norm == expected_norm:
        return True
    if not urlparse(expected_norm).path:
        return False
    return actual_norm.endswith(expected_norm) or expected_norm.endswith(
        actual_norm
    )


def wait_for_docs_url(
    expected_url: str,
    timeout: float = 20,
) -> tuple[int, str, str]:
    """等待任一浏览器打开期望的文档 URL。"""
    expected_host = urlparse(expected_url).netloc
    deadline = time.monotonic() + timeout
    last_titles: list[str] = []
    while time.monotonic() < deadline:
        last_titles = []
        for hwnd in visible_browser_windows():
            title = win32gui.GetWindowText(hwnd)
            last_titles.append(title)
            url = browser_url(hwnd, host=expected_host)
            if urls_match(url, expected_url):
                return hwnd, title, url
        time.sleep(0.2)
    raise TimeoutError(
        f"{timeout} 秒内未打开期望文档：{expected_url}；"
        f"当前浏览器标题：{last_titles}"
    )
