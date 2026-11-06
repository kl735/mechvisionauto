# coding: utf-8
"""Mech-Vision 主窗口 Page Object。"""

from __future__ import annotations

from pywinauto import Application

from pages.project_editor_page import ProjectEditorPage
from pages.project_list_page import ProjectListPage
from pages.step_library_page import StepLibraryPage


class MainWindowPage:
    """主窗口容器：统一持有 UIA 根窗口，并组合各功能区域。"""

    def __init__(self, main_window, timeout: float = 60) -> None:
        self.main_window = main_window
        self.timeout = timeout
        self.step_library = StepLibraryPage(main_window, timeout)
        self.project_list = ProjectListPage(main_window, timeout)
        self.project_editor = ProjectEditorPage(main_window, timeout)

    @classmethod
    def attach(cls, handle: int, timeout: float = 60) -> "MainWindowPage":
        """使用原生窗口句柄连接 UIA 主窗口。"""
        uia_app = Application(backend="uia").connect(handle=handle)
        main_window = uia_app.window(handle=handle)
        main_window.wait("exists visible", timeout=timeout)
        return cls(main_window, timeout)

    @property
    def handle(self) -> int:
        """返回主窗口原生句柄。"""
        return self.main_window.handle

    def exists(self, timeout: float = 5) -> bool:
        """主窗口是否存在。"""
        return self.main_window.exists(timeout=timeout)

    def focus(self) -> None:
        """将 Mech-Vision 主窗口置于前台。"""
        self.main_window.set_focus()

    def menu_item(self, title: str):
        """按标题定位主菜单项。"""
        return self.main_window.child_window(
            title=title,
            control_type="MenuItem",
        )

    def toolbar(self):
        """定位主窗口顶部工具栏。"""
        toolbar = self.main_window.child_window(
            title="Toolbar",
            control_type="ToolBar",
        )
        toolbar.wait("exists", timeout=self.timeout)
        return toolbar

    def toolbar_button(self, title: str):
        """按标题定位顶部工具栏按钮。"""
        return self.toolbar().child_window(
            title=title,
            control_type="Button",
        )
