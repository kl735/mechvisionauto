# coding: utf-8
"""Mech-Vision 工程编辑区 Page Object（含流程画布及画布 Step 右键菜单）。"""

from __future__ import annotations

import time

from pywinauto import Application

from utils.window_helper import (
    process_id_from_window,
    visible_process_windows,
    wait_window_hidden,
)


STEP_CONTEXT_MENU_CLASS = "mmind::ContextMenu"


class StepContextMenu:
    """封装工程编辑区画布中右键 Step 弹出的菜单（复制、剪切、粘贴、删除等）。"""

    def __init__(self, window, timeout: float = 5) -> None:
        self.window = window
        self.timeout = timeout

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        timeout: float = 5,
    ) -> "StepContextMenu":
        """等待同一进程中的画布 Step 右键菜单出现。"""
        process_id = process_id_from_window(reference_hwnd)
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            for hwnd in visible_process_windows(process_id):
                app = Application(backend="uia").connect(handle=hwnd)
                window = app.window(handle=hwnd)
                if (
                    window.exists(timeout=0.2)
                    and window.element_info.class_name
                    == STEP_CONTEXT_MENU_CLASS
                ):
                    return cls(window, timeout)
            time.sleep(0.1)

        raise TimeoutError("未出现画布 Step 右键菜单")

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


class ProjectEditorPage:
    """封装工程编辑区、流程画布和运行操作。"""

    def __init__(self, main_window, timeout: float = 60) -> None:
        self.main_window = main_window
        self.timeout = timeout

    def dock(self):
        """定位工程编辑区停靠窗口。"""
        editor = self.main_window.child_window(
            title="工程编辑区",
            class_name="mmind::tailor_impl::TDockWidget",
            control_type="Window",
        )
        editor.wait("exists", timeout=self.timeout)
        return editor

    def canvas(self):
        """定位 Step 流程画布。"""
        canvas = self.dock().child_window(
            class_name="mmind::ScaleGraphicsView",
            control_type="Group",
        )
        canvas.wait("exists", timeout=self.timeout)
        return canvas

    def canvas_point(
        self,
        x_ratio: float = 0.5,
        y_ratio: float = 0.5,
    ) -> tuple[int, int]:
        """按画布宽高比例计算一个屏幕坐标。"""
        rectangle = self.canvas().rectangle()
        return (
            round(rectangle.left + rectangle.width() * x_ratio),
            round(rectangle.top + rectangle.height() * y_ratio),
        )

    def wait_for_step_context_menu(
        self,
        timeout: float = 5,
    ) -> StepContextMenu:
        """等待并返回画布 Step 右键菜单对象。"""
        return StepContextMenu.wait_for_open(
            self.main_window.handle,
            timeout=timeout,
        )

    def run_button(self):
        """定位“运行”按钮。"""
        return self.dock().child_window(
            title="运行",
            control_type="Button",
        )

    def continuous_run_button(self):
        """定位“连续运行”按钮。"""
        return self.dock().child_window(
            title="连续运行",
            control_type="Button",
        )

    def debug_output_checkbox(self):
        """定位“调试输出”复选框。"""
        return self.dock().child_window(
            title="调试输出",
            control_type="CheckBox",
        )
