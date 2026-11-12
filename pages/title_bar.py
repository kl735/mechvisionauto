# coding: utf-8
"""Mech-Vision 主窗口标题栏 Page Object。"""

from pages.accuracy_error_analysis_page import AccuracyErrorAnalysisPage
from pages.deep_learning_model_package_manager_page import DeepLearningModelPackageManagerPage
from pages.python_package_manager_page import PythonPackageManagerPage


class TitleBar:
    """封装主窗口标题栏。"""

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

    def menu_bar(self):
        """通过 ClassName 和 ControlType 定位 Qt 主菜单栏。 Mech-Vision(蓝色字体)前的控件"""
        menu_bar = self.window.child_window(
            class_name="QMenuBar",
            control_type="MenuBar",
        )
        menu_bar.wait(
            "exists visible",
            timeout=self.timeout,
        )
        return menu_bar.wrapper_object()

    def top_menu_items(self) -> list:
        """返回 Qt 主菜单栏中的全部一级菜单项。"""
        return self.menu_bar().children(control_type="MenuItem")

    def top_menu_names(self) -> list[str]:
        """返回全部一级菜单项名称。"""
        return [
            item.window_text().strip()
            for item in self.top_menu_items()
            if item.window_text().strip()
        ]

    def top_menu_item(self, title: str):
        """按名称返回指定的一级菜单项。"""
        for item in self.top_menu_items():
            if item.window_text().strip() == title:
                return item
        raise RuntimeError(
            f"未找到一级菜单：{title!r}，"
            f"当前一级菜单：{self.top_menu_names()}"
        )

    def menu_select(self, path: str, exact: bool = True) -> None:
        """通过路径选择任意层级的 Qt 菜单项。"""
        menu_host = self.menu_bar().parent()
        menu_host.menu_select(path, exact=exact)

    def click_popup_menu_item(
        self,
        top_menu_title: str,
        item_title: str,
    ) -> None:
        """通过非阻塞点击方式选择会打开阻塞式窗口的菜单项。"""
        self.window.set_focus()
        self.top_menu_item(top_menu_title).click_input()
        menu_item = self.window.child_window(
            title=item_title,
            control_type="MenuItem",
        )
        menu_item.wait(
            "exists visible enabled ready",
            timeout=min(self.timeout, 10),
        )
        menu_item.wrapper_object().click_input()

    def open_accuracy_error_analysis(
        self,
    ) -> AccuracyErrorAnalysisPage:
        """从工具箱菜单打开并返回误差分析页面对象。"""
        self.menu_select("工具箱(T)->精度误差分析工具")
        return AccuracyErrorAnalysisPage.wait_for_open(
            reference_hwnd=self.window.handle,
            timeout=min(self.timeout, 10),
        )

    def open_python_package_manager(
        self,
    ) -> PythonPackageManagerPage:
        """从工具箱菜单打开并返回 Python 包管理工具页面对象。"""
        self.click_popup_menu_item(
            "工具箱(T)",
            "Python包管理工具",
        )
        return PythonPackageManagerPage.wait_for_open(
            reference_hwnd=self.window.handle,
            timeout=min(self.timeout, 10),
        )

    def open_deep_learning_model_package_manager(
        self,
    ) -> DeepLearningModelPackageManagerPage:
        """从深度学习菜单打开并返回模型包管理页面对象。"""
        self.click_popup_menu_item(
            "深度学习(D)",
            "深度学习模型包管理工具",
        )
        return DeepLearningModelPackageManagerPage.wait_for_open(
            reference_hwnd=self.window.handle,
            timeout=min(self.timeout, 10),
        )