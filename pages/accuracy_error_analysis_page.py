# coding: utf-8
"""“误差分析”工具窗口 Page Object。"""

from __future__ import annotations

import time

from pywinauto import Application

from utils.window_helper import (
    process_id_from_window,
    visible_process_windows,
    wait_window_hidden,
)


class AccuracyErrorAnalysisPage:
    """封装“精度误差分析工具”打开的“误差分析”窗口。"""

    TITLE = "误差分析"
    CLASS_NAME = "mmind::Dialog"
    AUTOMATION_ID = "mmind__Dialog"

    def __init__(self, window, timeout: float = 10) -> None:
        self.window = window
        self.timeout = timeout
        self._validate_window()

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        timeout: float = 10,
    ) -> "AccuracyErrorAnalysisPage":
        """等待同一进程中的“误差分析”窗口出现。"""
        process_id = process_id_from_window(reference_hwnd)
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            for hwnd in visible_process_windows(process_id):
                if hwnd == reference_hwnd:
                    continue
                try:
                    app = Application(backend="uia").connect(handle=hwnd)
                    window = app.window(handle=hwnd)
                    info = window.element_info
                    if (
                        info.name == cls.TITLE
                        and info.class_name == cls.CLASS_NAME
                        and info.automation_id == cls.AUTOMATION_ID
                    ):
                        return cls(window, timeout)
                except Exception:
                    continue
            time.sleep(0.1)

        raise TimeoutError(f"未出现窗口：{cls.TITLE}")

    def _validate_window(self) -> None:
        """确认传入窗口确实是“误差分析”窗口。"""
        info = self.window.element_info
        actual = (
            info.name,
            info.class_name,
            info.automation_id,
        )
        expected = (
            self.TITLE,
            self.CLASS_NAME,
            self.AUTOMATION_ID,
        )
        if actual != expected:
            raise ValueError(
                "传入窗口不是误差分析窗口："
                f"期望 {expected!r}，实际 {actual!r}"
            )

    @property
    def handle(self) -> int:
        """返回误差分析窗口原生句柄。"""
        return self.window.handle

    @property
    def element_info(self):
        """返回误差分析窗口 UIA 元素信息。"""
        return self.window.element_info

    def exists(self, timeout: float = 1) -> bool:
        """误差分析窗口是否存在。"""
        return self.window.exists(timeout=timeout)

    def is_visible(self) -> bool:
        """误差分析窗口当前是否可见。"""
        return self.exists() and self.window.is_visible()

    def focus(self) -> None:
        """将误差分析窗口置于前台。"""
        self.window.set_focus()

    def print_control_identifiers(self) -> None:
        """打印误差分析窗口完整控件树。"""
        self.window.print_control_identifiers()

    def close_button(self):
        """定位右上角关闭按钮。"""
        button = self.window.child_window(
            auto_id="mmind__Dialog.dialogFrame.titleBarWidget.closeBtn",
            control_type="Button",
        )
        button.wait(
            "exists visible enabled ready",
            timeout=self.timeout,
        )
        return button

    def navigation_item(self, title: str):
        """按名称定位左侧导航项（工具介绍、相机、机器人等）。"""
        label = self.window.child_window(
            title=title,
            control_type="Text",
        )
        label.wait("exists visible", timeout=self.timeout)
        return label.wrapper_object().parent()

    def select_navigation(self, title: str) -> None:
        """点击左侧指定导航项。"""
        self.navigation_item(title).click_input()

    def option_button(self, title: str, found_index: int = 0):
        """按文字和索引定位当前页面中的选项按钮。"""
        option = self.window.child_window(
            title=title,
            control_type="CheckBox",
            found_index=found_index,
        )
        option.wait(
            "exists visible enabled ready",
            timeout=self.timeout,
        )
        return option

    def evaluate_button(self):
        """定位“评估影响因素”按钮。"""
        button = self.window.child_window(
            title="评估影响因素",
            control_type="Button",
        )
        button.wait(
            "exists visible enabled ready",
            timeout=self.timeout,
        )
        return button

    def close(self) -> None:
        """关闭误差分析窗口并等待窗口隐藏。"""
        if not self.is_visible():
            return
        hwnd = self.handle
        self.close_button().click_input()
        wait_window_hidden(hwnd, self.timeout)
