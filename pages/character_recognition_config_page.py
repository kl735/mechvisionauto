# coding: utf-8
"""AI 字符识别配置向导 Page Object。"""

from __future__ import annotations

import time

import win32gui  # pyright: ignore[reportMissingModuleSource]
from pywinauto import Application, keyboard

from pages.message_box_page import MessageBoxPage
from utils.window_helper import (
    process_id_from_window,
    visible_process_windows,
    wait_window_closed,
)


class TargetRegionEditorPanel:
    """右侧“设置目标区域”编辑页面。"""

    ROOT_CLASS = "mmind::QuickAiRoiEditor"

    def __init__(self, stack_panel, timeout: float = 10) -> None:
        self.stack_panel = stack_panel
        self.timeout = timeout

    def root(self):
        """定位 QStackedWidget 当前显示的目标区域编辑页。"""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            for control in self.stack_panel.children():
                if (
                    control.element_info.class_name == self.ROOT_CLASS
                    and control.is_visible()
                ):
                    return control
            time.sleep(0.1)
        raise TimeoutError("目标区域编辑页未打开")

    def control(
        self,
        control_type: str,
        title: str | None = None,
        class_name: str | None = None,
        found_index: int = 0,
    ):
        """在目标区域编辑页内定位可见控件。"""
        controls = self.root().descendants(control_type=control_type)
        matches = [
            control
            for control in controls
            if control.is_visible()
            and (
                title is None
                or control.window_text() == title
            )
            and (
                class_name is None
                or control.element_info.class_name == class_name
            )
        ]
        if len(matches) <= found_index:
            raise RuntimeError(
                f"目标区域编辑页未找到控件：type={control_type!r}, "
                f"title={title!r}, class={class_name!r}, "
                f"index={found_index}"
            )
        return matches[found_index]

    def show_character_size_checkbox(self):
        """定位“显示字符大小区域”复选框。"""
        return self.control("CheckBox", class_name="QCheckBox")

    def all_target_region_radio(self):
        """定位“全部为目标区域”。"""
        return self.control("RadioButton", title="全部为目标区域")

    def custom_target_region_radio(self):
        """定位“自定义目标区域”。"""
        return self.control("RadioButton", title="自定义目标区域")

    def rectangle_button(self):
        """定位矩形目标区域工具。"""
        return self.control("CheckBox", title="矩形")

    def ring_button(self):
        """定位圆环目标区域工具。"""
        return self.control("CheckBox", title="圆环")

    def mask_region_button(self):
        """定位“设置屏蔽区域”工具。"""
        return self.control("CheckBox", title="设置屏蔽区域")

    def save_button(self):
        """定位“保存并使用”按钮。"""
        return self.control("Button", title="保存并使用")

    def cancel_button(self):
        """定位“取消”按钮。"""
        return self.control("Button", title="取消")

    def set_show_character_size(self, enabled: bool) -> None:
        """设置是否显示字符大小区域。"""
        checkbox = self.show_character_size_checkbox()
        current = bool(checkbox.get_toggle_state())
        if current != enabled:
            checkbox.click_input()

    def select_all_target_region(self) -> None:
        """选择全部区域作为目标区域。"""
        self.all_target_region_radio().click_input()

    def select_custom_target_region(self) -> None:
        """选择自定义目标区域。"""
        self.custom_target_region_radio().click_input()

    def select_rectangle_tool(self) -> None:
        """选择矩形目标区域工具。"""
        self.rectangle_button().click_input()

    def select_ring_tool(self) -> None:
        """选择圆环目标区域工具。"""
        self.ring_button().click_input()

    def toggle_mask_region(self) -> None:
        """切换设置屏蔽区域工具。"""
        self.mask_region_button().click_input()

    def save(self) -> None:
        """保存目标区域设置并返回默认配置页。"""
        self.save_button().click_input()

    def cancel(self) -> None:
        """取消目标区域编辑并返回默认配置页。"""
        self.cancel_button().click_input()


class CharacterRecognitionConfigPage:
    """封装 AI 字符识别配置窗口中的模型列表操作。"""

    CONFIG_PAGE_CLASSES = {
        "mmind::QuickAiNavigator",
        TargetRegionEditorPanel.ROOT_CLASS,
    }

    def __init__(self, window, timeout: float = 10) -> None:
        self.window = window
        self.timeout = timeout

    def new_model_button(self):
        """定位模型列表右上角的“新建”按钮。"""
        button = self.window.child_window(
            title="新建",
            control_type="Button",
        )
        button.wait("exists enabled visible", timeout=self.timeout)
        return button

    def model_list(self):
        """定位左侧模型列表。"""
        model_list = self.window.child_window(
            control_type="List",
            found_index=0,
        )
        model_list.wait("exists visible", timeout=self.timeout)
        return model_list

    def model_items(self):
        """返回模型列表中的全部模型项。"""
        return self.model_list().descendants(control_type="ListItem")

    def config_panel(self):
        """定位右侧内层 QStackedWidget 模型配置区域。"""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            candidates = self.window.descendants(control_type="Custom")
            for panel in candidates:
                if (
                    panel.element_info.class_name != "QStackedWidget"
                    or not panel.is_visible()
                ):
                    continue
                direct_children = panel.children()
                if any(
                    child.is_visible()
                    and child.element_info.class_name
                    in self.CONFIG_PAGE_CLASSES
                    for child in direct_children
                ):
                    return panel
            time.sleep(0.2)
        raise TimeoutError("未定位到右侧 QStackedWidget 模型配置区域")

    def config_controls(self, visible_only: bool = True):
        """返回右侧配置区域下的控件。"""
        controls = self.config_panel().descendants()
        if visible_only:
            controls = [
                control for control in controls if control.is_visible()
            ]
        return controls

    def config_control(
        self,
        control_type: str,
        title: str | None = None,
        found_index: int = 0,
    ):
        """在右侧配置区域内按类型和标题定位控件。"""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            controls = self.config_panel().descendants(
                control_type=control_type,
            )
            matches = [
                control
                for control in controls
                if control.is_visible()
                and (
                    title is None
                    or control.window_text() == title
                )
            ]
            if len(matches) > found_index:
                return matches[found_index]
            time.sleep(0.2)
        raise TimeoutError(
            f"配置区域内未定位到控件：type={control_type!r}, "
            f"title={title!r}, index={found_index}"
        )

    def target_region_edit_button(self):
        """定位“设置目标区域”下的编辑按钮。"""
        return self.config_control("Button", title="编辑")

    def open_target_region_editor(self) -> TargetRegionEditorPanel:
        """点击“编辑”并返回目标区域编辑页。"""
        self.target_region_edit_button().click_input()
        editor = TargetRegionEditorPanel(
            self.config_panel(),
            timeout=self.timeout,
        )
        editor.root()
        return editor

    def confidence_spinner(self):
        """定位置信度阈值输入框。"""
        return self.config_control("Spinner")

    def recognition_object_combo(self):
        """定位“识别对象”下拉框。"""
        return self.config_control("ComboBox", found_index=0)

    def separator_combo(self):
        """定位“拼接间隔符”下拉框。"""
        return self.config_control("ComboBox", found_index=1)

    def single_capture_button(self):
        """定位“单次采集”按钮。"""
        return self.config_control("Button", title="单次采集")

    def continuous_capture_checkbox(self):
        """定位“连续采集”复选框。"""
        return self.config_control("CheckBox", title="连续采集")

    def create_model(self) -> tuple[int, int]:
        """点击“新建”，等待模型数量增加并返回创建前后的数量。"""
        before_count = len(self.model_items())
        self.new_model_button().click_input()

        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            after_count = len(self.model_items())
            if after_count > before_count:
                return before_count, after_count
            time.sleep(0.2)

        raise TimeoutError(
            f"点击“新建”后模型数量没有增加，创建前数量：{before_count}"
        )

    def _visible_process_windows(self) -> list[int]:
        """返回配置向导所属进程中的可见顶层窗口句柄。"""
        process_id = process_id_from_window(self.window.handle)
        return visible_process_windows(process_id)

    def click_model_menu(
        self,
        model_index: int,
        menu_title: str,
    ) -> None:
        """右键指定模型并点击菜单项。"""
        items = self.model_items()
        if not items:
            raise RuntimeError("模型列表为空，无法执行右键菜单")

        try:
            item = items[model_index]
        except IndexError as error:
            raise IndexError(
                f"模型索引超出范围：{model_index}，当前数量：{len(items)}"
            ) from error

        item.select()
        keyboard.send_keys("+{F10}")

        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            for hwnd in self._visible_process_windows():
                if "Popup" not in win32gui.GetClassName(hwnd):
                    continue
                popup_app = Application(backend="uia").connect(handle=hwnd)
                menu_item = popup_app.window(handle=hwnd).child_window(
                    title=menu_title,
                    control_type="MenuItem",
                )
                if menu_item.exists(timeout=0.2):
                    menu_item.click_input()
                    return
            time.sleep(0.1)
        raise TimeoutError(f"模型右键菜单中未找到：{menu_title!r}")

    def _open_rename_dialog(self, model_index: int):
        """右键指定模型，通过菜单打开“重命名”对话框。"""
        self.click_model_menu(model_index, "重命名")
        return self._wait_for_rename_dialog()

    def _wait_for_rename_dialog(self):
        """等待并返回“重命名”对话框。"""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            for hwnd in self._visible_process_windows():
                if win32gui.GetWindowText(hwnd) != "重命名":
                    continue
                dialog_app = Application(backend="uia").connect(handle=hwnd)
                dialog = dialog_app.window(handle=hwnd)
                if dialog.exists(timeout=0.2):
                    return dialog
            time.sleep(0.1)
        raise TimeoutError("未出现模型“重命名”对话框")

    def _wait_window_closed(self, hwnd: int) -> None:
        """使用原生句柄等待窗口销毁，避免 UIA 访问失效元素。"""
        wait_window_closed(hwnd, self.timeout)

    def rename_model(self, new_name: str, model_index: int = -1) -> str:
        """修改模型名称，再次打开重命名框读取名称进行验证。"""
        if not new_name.strip():
            raise ValueError("模型名称不能为空")

        dialog = self._open_rename_dialog(model_index)
        name_edit = dialog.child_window(control_type="Edit")
        name_edit.wait("exists enabled visible", timeout=self.timeout)
        name_edit.set_edit_text(new_name)
        dialog_handle = dialog.handle
        dialog.child_window(
            title="确定",
            control_type="Button",
        ).click_input()
        self._wait_window_closed(dialog_handle)

        verify_dialog = self._open_rename_dialog(model_index)
        verify_edit = verify_dialog.child_window(control_type="Edit")
        verify_edit.wait("exists visible", timeout=self.timeout)
        actual_name = verify_edit.get_value().strip()
        verify_dialog_handle = verify_dialog.handle
        verify_dialog.child_window(
            title="取消",
            control_type="Button",
        ).click_input()
        self._wait_window_closed(verify_dialog_handle)
        return actual_name

    def delete_model(
        self,
        model_index: int = -1,
    ) -> tuple[int, int, str]:
        """删除指定模型，返回删除前后数量及确认提示文本。"""
        before_count = len(self.model_items())
        if before_count == 0:
            raise RuntimeError("模型列表为空，无法删除")

        reference_hwnd = self.window.handle
        self.click_model_menu(model_index, "删除")
        message_box = MessageBoxPage.wait_for_open(
            reference_hwnd,
            timeout=self.timeout,
        )
        message = message_box.message()
        message_box.confirm()

        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            after_count = len(self.model_items())
            if after_count == before_count - 1:
                return before_count, after_count, message
            time.sleep(0.2)

        after_count = len(self.model_items())
        raise TimeoutError(
            "确认删除后模型数量没有减少："
            f"{before_count} -> {after_count}"
        )
