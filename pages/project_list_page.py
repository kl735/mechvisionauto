# coding: utf-8
"""Mech-Vision 工程列表区域 Page Object。"""

from __future__ import annotations

import time
from typing import TypeVar

from pywinauto import Application, keyboard

from utils.window_helper import (
    process_id_from_window,
    visible_process_windows,
    wait_window_hidden,
)


QMENU_CLASS = "QMenu"
TMenu = TypeVar("TMenu", bound="QMenuPopup")


class QMenuPopup:
    """封装工程列表中基于 QMenu 的右键弹出菜单。"""

    EXPECTED_ITEM = ""

    def __init__(self, window, timeout: float = 5) -> None:
        self.window = window
        self.timeout = timeout

    @classmethod
    def wait_for_open(
        cls: type[TMenu],
        reference_hwnd: int,
        expected_item: str | None = None,
        timeout: float = 5,
    ) -> TMenu:
        """等待同一进程中的目标 QMenu 出现并校验特征菜单项。"""
        target_item = (
            cls.EXPECTED_ITEM if expected_item is None else expected_item
        )
        process_id = process_id_from_window(reference_hwnd)
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            for hwnd in visible_process_windows(process_id):
                if hwnd == reference_hwnd:
                    continue
                try:
                    app = Application(backend="uia").connect(handle=hwnd)
                    window = app.window(handle=hwnd)
                    if not (
                        window.exists(timeout=0.2)
                        and window.element_info.class_name == QMENU_CLASS
                    ):
                        continue
                    menu = cls(window, timeout)
                    if not target_item or menu.has_item(target_item):
                        return menu
                except Exception:
                    continue
            time.sleep(0.1)

        raise TimeoutError(
            f"未出现包含 {target_item!r} 的 QMenu 右键菜单"
        )

    @property
    def handle(self) -> int:
        """返回 QMenu 的原生窗口句柄。"""
        return self.window.handle

    @property
    def element_info(self):
        """转发底层 UIA 元素信息。"""
        return self.window.element_info

    def print_control_identifiers(self) -> None:
        """打印当前 QMenu 的完整控件树。"""
        self.window.print_control_identifiers()

    def items(self, named_only: bool = True) -> list:
        """获取菜单下的所有 MenuItem 子控件。"""
        menu_items = self.window.wrapper_object().descendants(
            control_type="MenuItem",
        )
        if named_only:
            return [
                item
                for item in menu_items
                if item.window_text().strip()
            ]
        return menu_items

    def item_names(self) -> list[str]:
        """返回菜单中所有可见菜单项名称。"""
        return [
            item.window_text().strip()
            for item in self.items(named_only=True)
        ]

    def has_item(self, title: str) -> bool:
        """判断菜单中是否存在目标菜单项。"""
        for name in self.item_names():
            normalized = name.split("\t", maxsplit=1)[0].strip()
            if name == title or normalized == title or name.startswith(title):
                return True
        return False

    def item(self, title: str):
        """按标题定位菜单项（兼容带快捷键后缀的标题）。"""
        exact_item = self.window.child_window(
            title=title,
            control_type="MenuItem",
        )
        if exact_item.exists(timeout=0.3):
            return exact_item

        for candidate in self.items(named_only=True):
            text = candidate.window_text().strip()
            normalized = text.split("\t", maxsplit=1)[0].strip()
            if text == title or normalized == title or text.startswith(title):
                return self.window.child_window(
                    title=candidate.window_text(),
                    control_type="MenuItem",
                )

        raise RuntimeError(
            f"QMenu 中未找到菜单项：{title!r}，当前菜单项：{self.item_names()}"
        )

    def click_item(self, title: str) -> None:
        """点击目标菜单项并等待菜单关闭。"""
        hwnd = self.handle
        self.item(title).click_input()
        wait_window_hidden(hwnd, self.timeout)

    def close(self) -> None:
        """按 ESC 关闭当前右键菜单并等待隐藏。"""
        hwnd = self.handle
        keyboard.send_keys("{ESC}")
        wait_window_hidden(hwnd, self.timeout)


class SolutionContextMenu(QMenuPopup):
    """封装工程列表中方案节点的右键菜单。"""

    EXPECTED_ITEM = "新建工程"

    def close_solution_item(self):
        """定位“关闭方案”菜单项。"""
        return self.item("关闭方案")

    def open_solution_folder_item(self):
        """定位“打开方案文件夹”菜单项。"""
        return self.item("打开方案文件夹")

    def create_project_item(self):
        """定位“新建工程”菜单项。"""
        return self.item("新建工程")

    def autoload_solution_item(self):
        """定位“自动加载当前方案”菜单项。"""
        return self.item("自动加载当前方案")

    def rename_solution_item(self):
        """定位“重命名方案”菜单项。"""
        return self.item("重命名方案")

    def manage_permission_item(self):
        """定位“管理方案权限”菜单项。"""
        return self.item("管理方案权限")

    def backup_solution_item(self):
        """定位“备份方案”菜单项。"""
        return self.item("备份方案")

    def reset_project_id_item(self):
        """定位“重置工程编号”菜单项。"""
        return self.item("重置工程编号")


class ProjectContextMenu(QMenuPopup):
    """封装工程列表中工程节点的右键菜单。"""

    EXPECTED_ITEM = "删除工程"

    def close_project_item(self):
        """定位“关闭工程”菜单项（兼容快捷键后缀）。"""
        return self.item("关闭工程")

    def open_project_folder_item(self):
        """定位“打开工程文件夹”菜单项。"""
        return self.item("打开工程文件夹")

    def rename_project_item(self):
        """定位“重命名工程”菜单项。"""
        return self.item("重命名工程")

    def delete_project_item(self):
        """定位“删除工程”菜单项。"""
        return self.item("删除工程")

    def copy_project_item(self):
        """定位“创建工程副本”菜单项。"""
        return self.item("创建工程副本")

    def backup_solution_item(self):
        """定位“备份方案”菜单项。"""
        return self.item("备份方案")


class DeleteProjectDialog:
    """封装右键点击“删除工程”后弹出的 StyledMessageBox 确认弹窗。"""

    MESSAGE_BOX_CLASS = "mmind::StyledMessageBox"
    EXPECTED_TEXT = "确定删除所选工程"

    def __init__(self, window, timeout: float = 5) -> None:
        self.window = window
        self.timeout = timeout

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        timeout: float = 5,
    ) -> "DeleteProjectDialog":
        """等待同一进程中的删除工程确认框出现并校验提示文字。"""
        process_id = process_id_from_window(reference_hwnd)
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            for hwnd in visible_process_windows(process_id):
                if hwnd == reference_hwnd:
                    continue
                try:
                    app = Application(backend="uia").connect(handle=hwnd)
                    window = app.window(handle=hwnd)
                    if (
                        window.exists(timeout=0.2)
                        and window.element_info.class_name
                        == cls.MESSAGE_BOX_CLASS
                    ):
                        dialog = cls(window, timeout)
                        if cls.EXPECTED_TEXT in dialog.message_text():
                            return dialog
                except Exception:
                    continue

            try:
                app = Application(backend="uia").connect(process=process_id)
                window = app.window(
                    class_name=cls.MESSAGE_BOX_CLASS,
                    control_type="Window",
                    title="Mech-Vision",
                )
                if window.exists(timeout=0.2):
                    dialog = cls(window, timeout)
                    if cls.EXPECTED_TEXT in dialog.message_text():
                        return dialog
            except Exception:
                pass

            time.sleep(0.1)

        raise TimeoutError(
            f"未出现包含 {cls.EXPECTED_TEXT!r} 的删除工程确认框"
        )

    @property
    def handle(self) -> int:
        """返回确认弹窗的原生窗口句柄。"""
        return self.window.handle

    # @property
    # def element_info(self):
    #     """转发底层 UIA 元素信息。"""
    #     return self.window.element_info

    # def print_control_identifiers(self) -> None:
    #     """打印删除工程确认弹窗的完整控件树。"""
    #     self.window.print_control_identifiers()

    def message_text(self) -> str:
        """获取确认弹窗中的可见提示文本。"""
        texts = [
            control.window_text().strip()
            for control in self.window.wrapper_object().descendants(
                control_type="Text"
            )
            if control.is_visible() and control.window_text().strip()
        ]
        return "\n".join(dict.fromkeys(texts))

    def delete_button(self):
        """定位“删除”按钮。"""
        button = self.window.child_window(
            title="删除",
            control_type="Button",
        )
        button.wait("exists", timeout=self.timeout)
        return button

    def cancel_button(self):
        """定位“取消”按钮。"""
        button = self.window.child_window(
            title="取消",
            control_type="Button",
        )
        button.wait("exists", timeout=self.timeout)
        return button

    def confirm_delete(self) -> None:
        """点击“删除”按钮并等待弹窗关闭。"""
        hwnd = self.handle
        self.delete_button().click_input()
        wait_window_hidden(hwnd, self.timeout)

    def cancel(self) -> None:
        """点击“取消”按钮并等待弹窗关闭。"""
        hwnd = self.handle
        self.cancel_button().click_input()
        wait_window_hidden(hwnd, self.timeout)


class ProjectListPage:
    """封装工程列表停靠窗口及工程树操作。"""

    def __init__(self, main_window, timeout: float = 60) -> None:
        self.main_window = main_window
        self.timeout = timeout

    def dock(self):
        """定位工程列表停靠窗口。"""
        project_list = self.main_window.child_window(
            title="工程列表",
            class_name="mmind::tailor_impl::TDockWidget",
            control_type="Window",
        )
        project_list.wait("exists", timeout=self.timeout)
        return project_list

    def tree(self):
        """定位工程树。"""
        tree = self.dock().child_window(control_type="Tree")
        tree.wait("exists", timeout=self.timeout)
        return tree

    def title_bar(self):
        """定位工程列表标题栏。"""
        title_bar = self.dock().child_window(
            class_name="mmind::TitleBarWithGroupBtn",
            control_type="Group",
        )
        title_bar.wait("exists", timeout=self.timeout)
        return title_bar

    def title_label(self):
        """定位标题栏中的“工程列表”文本。"""
        title = self.title_bar().child_window(
            title="工程列表",
            control_type="Text",
        )
        title.wait("exists", timeout=self.timeout)
        return title

    def title_buttons(self) -> list:
        """返回标题栏中从左到右排列的无名称按钮。"""
        buttons = self.title_bar().wrapper_object().descendants(
            control_type="Button",
        )
        visible_buttons = [
            button
            for button in buttons
            if button.is_visible() and button.rectangle().width() > 0
        ]
        return sorted(
            visible_buttons,
            key=lambda button: button.rectangle().left,
        )

    def left_title_button(self):
        """定位标题栏左侧按钮。"""
        buttons = self.title_buttons()
        if not buttons:
            raise RuntimeError("工程列表标题栏中未找到左侧按钮")
        return buttons[0]

    def right_title_button(self):
        """定位标题栏右侧按钮。"""
        buttons = self.title_buttons()
        if len(buttons) < 2:
            raise RuntimeError("工程列表标题栏中未找到右侧按钮")
        return buttons[-1]

    def tree_items(self, named_only: bool = False) -> list:
        """返回工程树中的节点，可选择过滤无名称占位节点。"""
        items = self.tree().wrapper_object().descendants(
            control_type="TreeItem",
        )
        if named_only:
            return [
                item
                for item in items
                if item.window_text().strip()
            ]
        return items

    def project_names(self) -> list[str]:
        """返回当前工程树中的所有工程名称（自动去除未保存星号前缀）。"""
        names: list[str] = []
        for item in self.tree_items(named_only=True):
            text = item.window_text().strip().lstrip("*")
            if text.startswith("工程"):
                names.append(text)
        return names

    def item(self, title: str):
        """按标题定位工程树节点。"""
        return self.tree().child_window(
            title=title,
            control_type="TreeItem",
        )

    def locate(self, project_name: str):
        """定位工程；兼容名称前带星号的未保存状态。"""
        for title in (project_name, f"*{project_name}"):
            project = self.item(title)
            if project.exists(timeout=1):
                return project
        raise RuntimeError(f"工程列表中未找到：{project_name}")

    def select(self, project_name: str) -> None:
        """单击工程节点并等待画布切换。"""
        self.main_window.set_focus()
        self.locate(project_name).click_input()
        time.sleep(0.8)

    def open_solution_menu(
        self,
        solution_name: str,
        timeout: float = 5,
    ) -> SolutionContextMenu:
        """右键点击方案节点并返回方案右键菜单对象。"""
        self.main_window.set_focus()
        solution = self.locate(solution_name)
        solution.click_input(button="right")
        return SolutionContextMenu.wait_for_open(
            self.main_window.handle,
            timeout=timeout,
        )

    def open_project_menu(
        self,
        project_name: str,
        timeout: float = 5,
    ) -> ProjectContextMenu:
        """右键点击工程节点并返回工程右键菜单对象。"""
        self.main_window.set_focus()
        self.locate(project_name).click_input(button="right")
        return ProjectContextMenu.wait_for_open(
            self.main_window.handle,
            timeout=timeout,
        )

    def open_delete_project_dialog(
        self,
        project_name: str,
        timeout: float = 5,
    ) -> DeleteProjectDialog:
        """右键点击工程并点击“删除工程”，返回删除确认弹窗对象。"""
        project_menu = self.open_project_menu(project_name, timeout=timeout)
        project_menu.click_item("删除工程")
        return DeleteProjectDialog.wait_for_open(
            self.main_window.handle,
            timeout=timeout,
        )
