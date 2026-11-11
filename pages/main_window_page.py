# coding: utf-8
"""Mech-Vision 主窗口 Page Object。"""

from __future__ import annotations

import time

from pywinauto import Application

from pages.project_editor_page import ProjectEditorPage
from pages.project_list_page import ProjectListPage
from pages.step_library_page import StepLibraryPage
from pages.title_bar import TitleBar


class MainWindowPage:
    """主窗口容器：统一持有 UIA 根窗口，并组合各功能区域。"""

    def __init__(self, main_window, timeout: float = 60) -> None:
        self.main_window = main_window
        self.timeout = timeout
        self.step_library = StepLibraryPage(main_window, timeout)
        self.project_list = ProjectListPage(main_window, timeout)
        self.project_editor = ProjectEditorPage(main_window, timeout)
        self.title_bar = TitleBar(main_window, timeout)

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

    def step_param_dock(self):
        """定位右下角“步骤参数”停靠窗口。"""
        dock = self.main_window.child_window(
            title="步骤参数",
            control_type="Window",
        )
        dock.wait("exists visible", timeout=self.timeout)
        return dock

    def step_param_value_item(self, param_name: str, timeout: float = 10):
        """在“步骤参数”树中按参数名定位右侧对应的值单元格 TreeItem。"""
        dock = self.step_param_dock()
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            items = dock.wrapper_object().descendants(control_type="TreeItem")
            label_item = next(
                (
                    item
                    for item in items
                    if item.is_visible()
                    and item.window_text().strip() == param_name
                ),
                None,
            )
            if label_item is not None:
                label_rect = label_item.rectangle()
                for item in items:
                    rect = item.rectangle()
                    if (
                        item.is_visible()
                        and abs(rect.top - label_rect.top) <= 5
                        and rect.left >= label_rect.right - 5
                    ):
                        return item
            time.sleep(0.2)
        raise TimeoutError(
            f"“步骤参数”面板中未找到参数 {param_name!r} 的值单元格"
        )

    def open_config_wizard(self, timeout: float = 10) -> None:
        """通过 UIA 定位“步骤参数”中“模型名称”右侧单元格并点击“配置向导”按钮。"""
        value_item = self.step_param_value_item("模型名称", timeout=timeout)
        rect = value_item.rectangle()
        click_offset_x = round(rect.width() * 0.5)
        click_offset_y = round(rect.height() * 0.72)
        value_item.click_input(coords=(click_offset_x, click_offset_y))
