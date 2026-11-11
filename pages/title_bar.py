# coding: utf-8
"""Mech-Vision 主窗口标题栏 Page Object。"""

from pages.accuracy_error_analysis_page import AccuracyErrorAnalysisPage


class TitleBar:
    """封装主窗口标题栏及顶部工具相关控件。"""

    def __init__(self, window, timeout: float = 60) -> None:
        self.window = window
        self.timeout = timeout

    def root(self):
        """定位 Mech-Vision 原生标题栏。"""
        title_bar = self.window.child_window(
            title="Mech-Vision",
            auto_id="TitleBar",
            control_type="TitleBar",
        )
        title_bar.wait(
            "exists visible",
            timeout=self.timeout,
        )
        return title_bar

    def toolbox_menu_button(self):
        """定位顶部菜单栏中的“工具箱(T)”入口。"""
        return self.menu_item("工具箱(T)")

    def toolbar_menu_button(self):
        """兼容业务称呼“工具栏按钮”，实际 UI 名称为“工具箱(T)”。"""
        return self.toolbox_menu_button()

    def menu_item(self, title: str):
        """按名称定位主窗口顶部 QAction 菜单项。"""
        item = self.window.child_window(
            title=title,
            class_name="QAction",
            control_type="MenuItem",
        )
        item.wait(
            "exists visible enabled ready",
            timeout=self.timeout,
        )
        return item

    def accuracy_error_analysis_item(self):
        """定位工具箱菜单中的“精度误差分析工具”菜单项。"""
        return self.menu_item("精度误差分析工具")

    def open_toolbar_menu(self):
        """点击“工具箱(T)”并等待工具菜单展开。"""
        self.window.set_focus()
        self.toolbar_menu_button().click_input()
        item = self.accuracy_error_analysis_item()
        return item.wrapper_object().parent()

    def open_accuracy_error_analysis(
        self,
    ) -> AccuracyErrorAnalysisPage:
        """从工具箱菜单打开并返回误差分析页面对象。"""
        self.open_toolbar_menu()
        self.accuracy_error_analysis_item().click_input()
        return AccuracyErrorAnalysisPage.wait_for_open(
            reference_hwnd=self.window.handle,
            timeout=min(self.timeout, 10),
        )