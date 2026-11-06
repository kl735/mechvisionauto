# coding: utf-8
"""Mech-Vision 工程编辑区 Page Object。"""

from __future__ import annotations


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
