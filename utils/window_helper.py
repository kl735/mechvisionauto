# coding: utf-8
"""Windows 顶层窗口查询与等待工具。"""

from __future__ import annotations

import ctypes
import time

import win32gui  # pyright: ignore[reportMissingModuleSource]
import win32process  # pyright: ignore[reportMissingModuleSource]


def set_per_monitor_dpi_awareness() -> None:
    """使用真实屏幕坐标，避免多显示器缩放造成鼠标点击偏移。"""
    try:
        ctypes.windll.user32.SetThreadDpiAwarenessContext(
            ctypes.c_void_p(-4),
        )
    except (AttributeError, OSError):
        ctypes.windll.user32.SetProcessDPIAware()


def process_id_from_window(hwnd: int) -> int:
    """返回窗口所属进程 ID。"""
    _, process_id = win32process.GetWindowThreadProcessId(hwnd)
    return process_id


def visible_process_windows(process_id: int) -> list[int]:
    """返回指定进程中的可见顶层窗口句柄。"""
    handles: list[int] = []

    def collect(hwnd: int, _: object) -> bool:
        _, window_process_id = win32process.GetWindowThreadProcessId(hwnd)
        if (
            window_process_id == process_id
            and win32gui.IsWindowVisible(hwnd)
        ):
            handles.append(hwnd)
        return True

    win32gui.EnumWindows(collect, None)
    return handles


def wait_window_closed(hwnd: int, timeout: float = 10) -> None:
    """等待原生窗口句柄销毁。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not win32gui.IsWindow(hwnd):
            return
        time.sleep(0.1)
    raise TimeoutError(f"窗口未在 {timeout} 秒内关闭：handle={hwnd}")


def wait_window_hidden(hwnd: int, timeout: float = 10) -> None:
    """等待原生窗口隐藏或销毁。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if (
            not win32gui.IsWindow(hwnd)
            or not win32gui.IsWindowVisible(hwnd)
        ):
            return
        time.sleep(0.1)
    raise TimeoutError(f"窗口未在 {timeout} 秒内隐藏：handle={hwnd}")
