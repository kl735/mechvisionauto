# coding: utf-8
"""Mech-Vision 右键菜单 Page Object。"""

from __future__ import annotations

import time

from pywinauto import Application

from utils.window_helper import (
    process_id_from_window,
    visible_process_windows,
    wait_window_hidden,
)


CONTEXT_MENU_CLASS = "mmind::ContextMenu"


class ContextMenuPage:
    """封装复制、剪切、粘贴、删除等 Qt 右键菜单操作。"""

    def __init__(self, window, timeout: float = 5) -> None:
        self.window = window
        self.timeout = timeout

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        timeout: float = 5,
    ) -> "ContextMenuPage":
        """等待同一进程中的 Mech-Vision 右键菜单出现。"""
        process_id = process_id_from_window(reference_hwnd)
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            for hwnd in visible_process_windows(process_id):
                app = Application(backend="uia").connect(handle=hwnd)
                window = app.window(handle=hwnd)
                if (
                    window.exists(timeout=0.2)
                    and window.element_info.class_name == CONTEXT_MENU_CLASS
                ):
                    return cls(window, timeout)
            time.sleep(0.1)

        raise TimeoutError("未出现 Mech-Vision 右键菜单")

    @property
    def handle(self) -> int:
        """返回右键菜单的原生窗口句柄。"""
        return self.window.handle

    def item(self, title: str):
        """按标题定位一个菜单项。"""
        menu_item = self.window.child_window(
            title=title,
            control_type="MenuItem",
        )
        if menu_item.exists(timeout=self.timeout):
            return menu_item
        raise RuntimeError(f"右键菜单中未找到菜单项：{title!r}")

    def click_item(self, title: str) -> None:
        """点击菜单项并等待右键菜单关闭。"""
        hwnd = self.handle
        self.item(title).click_input()
        wait_window_hidden(hwnd, self.timeout)

    def delete(self) -> None:
        """点击“删除”菜单项。"""
        self.click_item("删除")
