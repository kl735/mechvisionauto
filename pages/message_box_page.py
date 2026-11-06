# coding: utf-8
"""Mech-Vision 通用模态提示框 Page Object。"""

from __future__ import annotations

import time

from pywinauto import Application

from utils.window_helper import (
    process_id_from_window,
    visible_process_windows,
    wait_window_closed,
)


MESSAGE_BOX_CLASS = "mmind::StyledMessageBox"


class MessageBoxPage:
    """封装 Mech-Vision 的确定、取消类模态提示框。"""

    def __init__(self, window, timeout: float = 10) -> None:
        self.window = window
        self.timeout = timeout

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        timeout: float = 10,
    ) -> "MessageBoxPage":
        """等待同一进程中的 StyledMessageBox 出现。"""
        process_id = process_id_from_window(reference_hwnd)
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            for hwnd in visible_process_windows(process_id):
                app = Application(backend="uia").connect(handle=hwnd)
                window = app.window(handle=hwnd)
                if (
                    window.exists(timeout=0.2)
                    and window.element_info.class_name == MESSAGE_BOX_CLASS
                ):
                    return cls(window, timeout)
            time.sleep(0.1)

        raise TimeoutError("未出现 Mech-Vision 模态提示框")

    @property
    def handle(self) -> int:
        """返回提示框原生句柄。"""
        return self.window.handle

    def message(self) -> str:
        """读取提示框中的可见文本。"""
        texts = [
            control.window_text().strip()
            for control in self.window.descendants(control_type="Text")
            if control.is_visible() and control.window_text().strip()
        ]
        return "\n".join(dict.fromkeys(texts))

    def button(self, *titles: str):
        """按候选标题定位第一个可用按钮。"""
        for title in titles:
            button = self.window.child_window(
                title=title,
                control_type="Button",
            )
            if button.exists(timeout=0.2):
                return button
        raise RuntimeError(f"提示框中未找到按钮：{titles!r}")

    def click_button(self, *titles: str) -> None:
        """点击按钮并等待提示框关闭。"""
        hwnd = self.handle
        self.button(*titles).click_input()
        wait_window_closed(hwnd, self.timeout)

    def confirm(self) -> None:
        """确认提示框。"""
        self.click_button("确定", "是", "是(Y)", "删除")

    def cancel(self) -> None:
        """取消提示框。"""
        self.click_button("取消", "否", "否(N)")
