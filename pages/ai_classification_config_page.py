# coding: utf-8
"""AI 分类（正反/有无）配置向导 Page Object。"""

from __future__ import annotations

import time

import win32gui
from pywinauto import Application, keyboard

from utils.window_helper import (
    process_id_from_window,
    visible_process_windows,
    wait_window_closed,
)


class DeleteModelDialog:
    """封装右键模型点击“删除”后弹出的确认弹窗。"""

    MESSAGE_BOX_CLASS = "mmind::StyledMessageBox"

    def __init__(self, window, timeout: float = 10) -> None:
        self.window = window
        self.timeout = timeout

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        timeout: float = 10,
    ) -> "DeleteModelDialog":
        """等待同一进程中的模型删除确认弹窗出现。"""
        process_id = process_id_from_window(reference_hwnd)
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            for hwnd in visible_process_windows(process_id):
                app = Application(backend="uia").connect(handle=hwnd)
                window = app.window(handle=hwnd)
                if (
                    window.exists(timeout=0.2)
                    and window.element_info.class_name
                    == cls.MESSAGE_BOX_CLASS
                ):
                    return cls(window, timeout)
            time.sleep(0.1)

        raise TimeoutError("未出现模型删除确认弹窗")

    @property
    def handle(self) -> int:
        """返回确认框原生句柄。"""
        return self.window.handle

    def message(self) -> str:
        """读取确认框中的可见提示文本。"""
        texts = [
            control.window_text().strip()
            for control in self.window.descendants(control_type="Text")
            if control.is_visible() and control.window_text().strip()
        ]
        return "\n".join(dict.fromkeys(texts))

    def button(self, *titles: str):
        """按候选标题定位按钮。"""
        for title in titles:
            button = self.window.child_window(
                title=title,
                control_type="Button",
            )
            if button.exists(timeout=0.2):
                return button
        raise RuntimeError(f"确认弹窗中未找到按钮：{titles!r}")

    def confirm(self) -> None:
        """点击确认/是/删除按钮并等待弹窗关闭。"""
        hwnd = self.handle
        self.button("确定", "是", "是(Y)", "删除").click_input()
        wait_window_closed(hwnd, self.timeout)

    def cancel(self) -> None:
        """点击取消/否按钮并等待弹窗关闭。"""
        hwnd = self.handle
        self.button("取消", "否", "否(N)").click_input()
        wait_window_closed(hwnd, self.timeout)


class AiClassificationTargetRegionEditorPanel:
    """AI 分类目标区域编辑页面。"""

    ROOT_CLASS = "mmind::QuickAiRoiEditor"

    def __init__(self, stack_panel, timeout: float = 10) -> None:
        self.stack_panel = stack_panel
        self.timeout = timeout

    def root(self):
        """定位当前显示的目标区域编辑页。"""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            for control in self.stack_panel.children():
                if (
                    control.element_info.class_name == self.ROOT_CLASS
                    and control.is_visible()
                ):
                    return control
            time.sleep(0.1)
        raise TimeoutError("AI 分类目标区域编辑页未打开")

    def control(self, control_type: str, title: str):
        """按标题定位编辑页内可见控件。"""
        matches = [
            control
            for control in self.root().descendants(
                control_type=control_type,
            )
            if control.is_visible() and control.window_text() == title
        ]
        if not matches:
            raise RuntimeError(
                f"AI 分类目标区域编辑页未找到控件："
                f"type={control_type!r}, title={title!r}"
            )
        return matches[0]

    def rectangle_button(self):
        """定位矩形目标区域工具。"""
        return self.control("CheckBox", "矩形")

    def circle_button(self):
        """定位圆形目标区域工具。"""
        return self.control("CheckBox", "圆形")

    def mask_region_button(self):
        """定位设置屏蔽区域工具。"""
        return self.control("CheckBox", "设置屏蔽区域")

    def save_button(self):
        """定位保存并使用按钮。"""
        return self.control("Button", "保存并使用")

    def cancel_button(self):
        """定位取消按钮。"""
        return self.control("Button", "取消")

    def select_rectangle_tool(self) -> None:
        """选择矩形目标区域工具。"""
        self.rectangle_button().click_input()

    def select_circle_tool(self) -> None:
        """选择圆形目标区域工具。"""
        self.circle_button().click_input()

    def toggle_mask_region(self) -> None:
        """切换设置屏蔽区域工具。"""
        self.mask_region_button().click_input()

    def save(self) -> None:
        """保存设置并返回默认配置页。"""
        self.save_button().click_input()

    def cancel(self) -> None:
        """取消设置并返回默认配置页。"""
        self.cancel_button().click_input()


class AiClassificationConfigPage:
    """封装“AI分类（正反/有无）”配置向导顶层窗口。"""

    TITLE = "AI分类（正反/有无）"
    CLASS_NAME = "mmind::Dialog"
    AUTOMATION_ID = "mmind__Dialog"
    CONFIG_PAGE_CLASSES = {
        "mmind::QuickAiNavigator",
        AiClassificationTargetRegionEditorPanel.ROOT_CLASS,
    }

    def __init__(self, window, timeout: float = 10) -> None:
        self.window = window
        self.timeout = timeout
        self._validate_window()

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        timeout: float = 10,
    ) -> "AiClassificationConfigPage":
        """等待同一进程中的 AI 分类配置向导出现。"""
        process_id = process_id_from_window(reference_hwnd)
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            for hwnd in visible_process_windows(process_id):
                app = Application(backend="uia").connect(handle=hwnd)
                window = app.window(handle=hwnd)
                info = window.element_info
                if (
                    info.name == cls.TITLE
                    and info.class_name == cls.CLASS_NAME
                    and info.automation_id == cls.AUTOMATION_ID
                ):
                    return cls(window, timeout)
            time.sleep(0.1)

        raise TimeoutError(f"未出现配置向导：{cls.TITLE}")

    def _validate_window(self) -> None:
        """确认传入窗口确实是 AI 分类配置向导。"""
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
                "传入窗口不是 AI 分类配置向导："
                f"期望 {expected!r}，实际 {actual!r}"
            )

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

    def model_count(self):
        """返回模型列表中的模型数量。"""
        return len(self.model_items())

    def model_item(self, model_index: int = 0):
        """按索引返回任意一个模型控件，支持负数索引。"""
        items = self.model_items()
        try:
            return items[model_index]
        except IndexError as error:
            raise IndexError(
                f"模型索引超出范围：{model_index}，"
                f"当前模型数量：{len(items)}"
            ) from error

    def first_model_item(self):
        """返回模型列表中的第一个模型项。"""
        return self.model_item(0)

    def last_model_item(self):
        """返回模型列表中的最后一个模型项。"""
        return self.model_item(-1)

    def first_model_name(self):
        """返回模型列表中的第一个模型名称。"""
        return self.first_model_item().window_text()

    def last_model_name(self):
        """返回模型列表中的最后一个模型名称。"""
        return self.last_model_item().window_text()

    def model_name(self, model_index: int = -1) -> str:
        """返回指定模型的名称。"""
        return self.model_item(model_index).window_text()

    def _open_create_copy_dialog(self, model_index: int):
        """通过右键菜单打开指定模型的“创建副本”对话框。"""
        self.click_model_menu(model_index, "创建副本")
        return self._wait_for_model_dialog("创建副本")

    def _open_rename_dialog(self, model_index: int):
        """通过右键菜单打开指定模型的重命名对话框。"""
        self.click_model_menu(model_index, "重命名")
        return self._wait_for_model_dialog("重命名")

    def _wait_for_model_dialog(self, title: str):
        """按窗口标题等待并返回模型操作对话框。"""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            for hwnd in self._visible_process_windows():
                if win32gui.GetWindowText(hwnd) != title:
                    continue
                dialog_app = Application(backend="uia").connect(handle=hwnd)
                dialog = dialog_app.window(handle=hwnd)
                if dialog.exists(timeout=0.2):
                    return dialog
            time.sleep(0.1)
        raise TimeoutError(f"未出现模型操作对话框：{title!r}")

    def _wait_window_closed(self, hwnd: int) -> None:
        """等待指定原生窗口销毁。"""
        wait_window_closed(hwnd, self.timeout)

    def create_model_copy(
        self,
        copy_name: str,
        model_index: int = 0,
    ) -> None:
        """为任意模型创建指定名称的副本。"""
        if not copy_name.strip():
            raise ValueError("模型副本名称不能为空")

        dialog = self._open_create_copy_dialog(model_index)
        name_edit = dialog.child_window(control_type="Edit")
        name_edit.wait("exists enabled visible", timeout=self.timeout)
        name_edit.set_edit_text(copy_name)

        dialog_handle = dialog.handle
        confirm_button = dialog.child_window(
            title="确定",
            control_type="Button",
        )
        confirm_button.wait(
            "exists enabled visible",
            timeout=self.timeout,
        )
        confirm_button.click_input()
        self._wait_window_closed(dialog_handle)

    def set_model_name(self, new_name: str, model_index: int = -1) -> None:
        """修改指定模型的名称。"""
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

    def cancel_model_rename(
        self,
        new_name: str,
        model_index: int = -1,
    ) -> None:
        """输入新名称后点击取消，不保存本次重命名。"""
        if not new_name.strip():
            raise ValueError("模型名称不能为空")

        dialog = self._open_rename_dialog(model_index)
        name_edit = dialog.child_window(control_type="Edit")
        name_edit.wait("exists enabled visible", timeout=self.timeout)
        name_edit.set_edit_text(new_name)
        dialog_handle = dialog.handle
        dialog.child_window(
            title="取消",
            control_type="Button",
        ).click_input()
        self._wait_window_closed(dialog_handle)

    def config_panel(self):
        """定位右侧内层 QStackedWidget 配置区域。"""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            candidates = self.window.descendants(control_type="Custom")
            for panel in candidates:
                if (
                    panel.element_info.class_name != "QStackedWidget"
                    or not panel.is_visible()
                ):
                    continue
                if any(
                    child.is_visible()
                    and child.element_info.class_name
                    in self.CONFIG_PAGE_CLASSES
                    for child in panel.children()
                ):
                    return panel
            time.sleep(0.2)
        raise TimeoutError("未定位到 AI 分类右侧 QStackedWidget 配置区域")

    def config_controls(self, visible_only: bool = True):
        """返回右侧配置区域内的控件。"""
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
        class_name: str | None = None,
        found_index: int = 0,
    ):
        """在右侧配置区域内定位指定控件。"""
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
                and (
                    class_name is None
                    or control.element_info.class_name == class_name
                )
            ]
            if len(matches) > found_index:
                return matches[found_index]
            time.sleep(0.2)
        raise TimeoutError(
            f"AI 分类配置区域内未定位到控件："
            f"type={control_type!r}, title={title!r}, "
            f"class={class_name!r}, index={found_index}"
        )

    def target_region_edit_button(self):
        """定位“设置目标区域”下的编辑按钮。"""
        return self.config_control("Button", title="编辑")

    def target_region_text(self):
        """通过“设置目标区域”的父节点，定位状态文本控件（如“未设置”/“已设置”）。"""
        groupbox = self.config_control("Text", title="设置目标区域").parent()
        for child in groupbox.children(control_type="Text"):
            text = child.window_text().strip()
            if child.is_visible() and text and text != "设置目标区域":
                return child
        raise RuntimeError("未在“设置目标区域”父节点下找到状态文本控件")

    def confidence_spinner(self):
        """定位置信度阈值输入框。"""
        return self.config_control("Spinner")

    def single_capture_button(self):
        """定位“单次采集”按钮。"""
        return self.config_control("Button", title="单次采集")

    def continuous_capture_checkbox(self):
        """定位“连续采集”复选框。"""
        return self.config_control("CheckBox", title="连续采集")

    def create_model(self) -> tuple[int, int]:
        """新建模型，并返回创建前后的模型数量。"""
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
        """打开指定模型的右键菜单并点击菜单项。"""
        item = self.model_item(model_index)
        self.window.set_focus()
        item.click_input()
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

    def open_delete_model_dialog(
        self,
        model_index: int = -1,
    ) -> DeleteModelDialog:
        """右键点击指定模型并点击“删除”，返回模型删除确认弹窗对象。"""
        self.click_model_menu(model_index, "删除")
        return DeleteModelDialog.wait_for_open(
            self.handle,
            timeout=self.timeout,
        )

    
    def category_panel(self, category: str):
        """按 ``OK`` 或 ``NG`` 定位类别区域。"""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            for control in self.config_panel().descendants():
                if (
                    control.element_info.class_name
                    == "mmind::CategoryWidget"
                    and control.is_visible()
                ):
                    texts = {
                        child.window_text()
                        for child in control.descendants()
                        if child.is_visible()
                    }
                    if category in texts:
                        return control
            time.sleep(0.1)
        raise RuntimeError(f"未定位到 AI 分类类别区域：{category!r}")

    def label_image_button(self, category: str):
        """定位指定类别区域中的“标注图像”按钮。"""
        panel = self.category_panel(category)
        buttons = [
            control
            for control in panel.descendants(control_type="Button")
            if control.is_visible() and control.window_text() == "标注图像"
        ]
        if not buttons:
            raise RuntimeError(
                f"{category!r} 类别区域中未找到“标注图像”按钮"
            )
        return buttons[0]

    def ok_label_button(self):
        """定位 OK 类别的标注图像按钮。"""
        return self.label_image_button("OK")

    def ng_label_button(self):
        """定位 NG 类别的标注图像按钮。"""
        return self.label_image_button("NG")

    def advanced_settings_checkbox(self):
        """定位高级设置复选框。"""
        return self.config_control(
            "CheckBox",
            class_name="QCheckBox",
        )

    def heatmap_checkbox(self):
        """定位热力图开关。"""
        return self.config_control(
            "CheckBox",
            class_name="mmind::SwitchButton",
        )

    def judgment_combo(self):
        """定位图像判定设置下拉框。"""
        return self.config_control("ComboBox")

    def set_judgment(self, value: str) -> None:
        """设置图像判定方式。"""
        allowed = {"全部为OK", "至少一个为OK"}
        if value not in allowed:
            raise ValueError(
                f"不支持的图像判定方式：{value!r}，可选值为 {allowed}"
            )
        self.judgment_combo().select(value)

    def open_target_region_editor(
        self,
    ) -> AiClassificationTargetRegionEditorPanel:
        """点击编辑并返回 AI 分类专用目标区域编辑对象。"""
        self.target_region_edit_button().click_input()
        editor = AiClassificationTargetRegionEditorPanel(
            self.config_panel(),
            timeout=self.timeout,
        )
        editor.root()
        return editor

    @property
    def handle(self) -> int:
        """返回配置向导原生窗口句柄。"""
        return self.window.handle

    def exists(self, timeout: float = 5) -> bool:
        """配置向导是否仍然存在。"""
        return self.window.exists(timeout=timeout)

    def title(self) -> str:
        """返回配置向导标题。"""
        return self.window.window_text()
