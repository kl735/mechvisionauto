# coding: utf-8
"""“深度学习模型包管理”窗口 Page Object。"""

from __future__ import annotations

import time
from pathlib import Path

from pywinauto import Application

from utils.window_helper import (
    process_id_from_window,
    visible_process_windows,
    wait_window_hidden,
)


class ModelPackageFileDialog:
    """封装导入模型包时打开的 Windows 文件选择窗口。"""

    TITLE = "选择文件"
    CLASS_NAME = "#32770"

    def __init__(self, window, timeout: float = 10) -> None:
        self.window = window
        self.timeout = timeout

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        timeout: float = 10,
    ) -> "ModelPackageFileDialog":
        """等待与模型包管理窗口同进程的文件选择窗口出现。"""
        process_id = process_id_from_window(reference_hwnd)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for hwnd in visible_process_windows(process_id):
                try:
                    app = Application(backend="uia").connect(handle=hwnd)
                    window = app.window(handle=hwnd)
                    info = window.element_info
                    if (
                        info.name == cls.TITLE
                        and info.class_name == cls.CLASS_NAME
                    ):
                        return cls(window, timeout)
                except Exception:
                    continue
            time.sleep(0.1)
        raise TimeoutError("未出现模型包文件选择窗口")

    def file_name_edit(self):
        """定位“文件名”输入框。"""
        edit = self.window.child_window(
            auto_id="1148",
            control_type="Edit",
        )
        edit.wait("exists visible enabled", timeout=self.timeout)
        return edit

    def open_button(self):
        """定位“打开”按钮。"""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            candidates = [
                control
                for control in self.window.descendants()
                if control.element_info.automation_id == "1"
                and control.is_visible()
                and control.is_enabled()
            ]
            split_buttons = [
                control
                for control in candidates
                if control.element_info.control_type == "SplitButton"
            ]
            if split_buttons:
                return split_buttons[0]
            if candidates:
                return candidates[-1]
            time.sleep(0.1)
        raise TimeoutError("文件选择窗口中未找到“打开”按钮")

    def cancel_button(self):
        """定位“取消”按钮。"""
        button = self.window.child_window(
            auto_id="2",
            control_type="Button",
        )
        button.wait("exists visible enabled", timeout=self.timeout)
        return button

    def select_file(self, file_path: str | Path) -> None:
        """输入模型包完整路径并点击“打开”。"""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"模型包不存在：{path}")
        self.file_name_edit().set_edit_text(str(path))
        self.open_button().click_input()

    def cancel(self) -> None:
        """取消文件选择。"""
        self.cancel_button().invoke()


class ModelPackageMessageBox:
    """封装模型包导入或删除过程中出现的提示框。"""

    CLASS_NAME = "mmind::StyledMessageBox"

    def __init__(self, window, timeout: float = 10) -> None:
        self.window = window
        self.timeout = timeout

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        timeout: float = 10,
    ) -> "ModelPackageMessageBox":
        """等待同一进程中的模型包提示框出现。"""
        process_id = process_id_from_window(reference_hwnd)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for hwnd in visible_process_windows(process_id):
                if hwnd == reference_hwnd:
                    continue
                try:
                    app = Application(backend="uia").connect(handle=hwnd)
                    window = app.window(handle=hwnd)
                    if window.element_info.class_name == cls.CLASS_NAME:
                        return cls(window, timeout)
                except Exception:
                    continue
            time.sleep(0.1)
        raise TimeoutError("未出现模型包提示框")

    @property
    def handle(self) -> int:
        """返回提示框原生句柄。"""
        return self.window.handle

    def text_contents(self) -> list[str]:
        """返回提示框中的全部非空文本。"""
        return [
            control.window_text().strip()
            for control in self.window.descendants(control_type="Text")
            if control.is_visible() and control.window_text().strip()
        ]

    def button(self, title: str):
        """按名称定位提示框按钮。"""
        button = self.window.child_window(
            title=title,
            control_type="Button",
        )
        button.wait("exists visible enabled", timeout=self.timeout)
        return button

    def confirm(self) -> None:
        """点击“确定”并等待提示框关闭。"""
        hwnd = self.handle
        self.button("确定").invoke()
        wait_window_hidden(hwnd, self.timeout)

    def cancel(self) -> None:
        """点击“取消”并等待提示框关闭。"""
        hwnd = self.handle
        self.button("取消").invoke()
        wait_window_hidden(hwnd, self.timeout)


class DeepLearningModelPackageManagerPage:
    """封装“深度学习模型包管理”窗口及其核心控件。"""

    TITLE = "Mech-Vision"
    CLASS_NAME = "mmind::DLModelPackManagementDialog"
    AUTOMATION_ID = "mmind__DLModelPackManagementDialog"
    CONTROL_TYPE = "Window"

    def __init__(self, window, timeout: float = 10) -> None:
        self.window = window
        self.timeout = timeout
        self._validate_window()

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        timeout: float = 10,
    ) -> "DeepLearningModelPackageManagerPage":
        """等待同一进程中的深度学习模型包管理窗口出现。"""
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
                        and info.control_type == cls.CONTROL_TYPE
                    ):
                        return cls(window, timeout)
                except Exception:
                    continue
            time.sleep(0.1)
        raise TimeoutError("未出现窗口：深度学习模型包管理")

    def _validate_window(self) -> None:
        """确认传入窗口是深度学习模型包管理窗口。"""
        info = self.window.element_info
        actual = (
            info.name,
            info.class_name,
            info.automation_id,
            info.control_type,
        )
        expected = (
            self.TITLE,
            self.CLASS_NAME,
            self.AUTOMATION_ID,
            self.CONTROL_TYPE,
        )
        if actual != expected:
            raise ValueError(
                "传入窗口不是深度学习模型包管理窗口："
                f"期望 {expected!r}，实际 {actual!r}"
            )

    @property
    def handle(self) -> int:
        """返回窗口原生句柄。"""
        return self.window.handle

    @property
    def element_info(self):
        """返回窗口 UIA 元素信息。"""
        return self.window.element_info

    def exists(self, timeout: float = 1) -> bool:
        """判断窗口是否存在。"""
        try:
            return self.window.exists(timeout=timeout)
        except Exception:
            return False

    def is_visible(self) -> bool:
        """判断窗口是否可见。"""
        return self.exists() and self.window.is_visible()

    def _control(self, auto_id: str, control_type: str):
        """按 AutomationId 和控件类型定位窗口内部控件。"""
        control = self.window.child_window(
            auto_id=auto_id,
            control_type=control_type,
        )
        control.wait("exists visible", timeout=self.timeout)
        return control

    def title_label(self):
        """定位“深度学习模型包管理”标题。"""
        return self._control(
            f"{self.AUTOMATION_ID}.titleBar.frame_titleBackground.title",
            "Text",
        )

    def close_button(self):
        """定位右上角关闭按钮。"""
        return self._control(
            f"{self.AUTOMATION_ID}."
            "titleBar.frame_titleBackground.btn_close",
            "Button",
        )

    def download_tip_label(self):
        """定位通用模型包下载提示文本。"""
        return self._control(
            f"{self.AUTOMATION_ID}."
            "frame_background.downloadTipWidget.tipMessage",
            "Text",
        )

    def open_cache_folder_button(self):
        """定位“打开缓存文件夹”按钮。"""
        return self._control(
            f"{self.AUTOMATION_ID}."
            "frame_background.btn_openCachedModelFolder",
            "Button",
        )

    def import_model_package_button(self):
        """定位“导入模型包”按钮。"""
        return self._control(
            f"{self.AUTOMATION_ID}.frame_background.btn_importModel",
            "Button",
        )

    def model_package_table(self):
        """定位模型包信息表格。"""
        return self._control(
            f"{self.AUTOMATION_ID}."
            "frame_background.tablewidget.tableView_modelPackInfo",
            "Table",
        )

    def table_header_names(self) -> list[str]:
        """返回表格第一行的全部表头名称。"""
        table = self.model_package_table().wrapper_object()
        return [
            header.window_text().strip()
            for header in table.descendants(control_type="Header")
            if header.is_visible() and header.window_text().strip()
        ]

    def table_rows(self) -> list[list[str]]:
        """按表格列数将所有模型包单元格整理为二维列表。"""
        column_count = len(self.table_header_names())
        if column_count == 0:   
            return []
        table = self.model_package_table().wrapper_object()
        values = [
            item.window_text().strip()
            for item in table.descendants(control_type="DataItem")
            if item.is_visible()
        ]
        return [
            values[index:index + column_count]
            for index in range(0, len(values), column_count)
            if len(values[index:index + column_count]) == column_count
        ]

    def model_names(self) -> list[str]:
        """返回表格中全部缓存模型包名称。"""
        return [row[0] for row in self.table_rows()]

    def has_model(self, model_name: str) -> bool:
        """判断表格中是否存在指定模型包。"""
        return model_name in self.model_names()

    def wait_for_model(
        self,
        model_name: str,
        present: bool = True,
        timeout: float | None = None,
    ) -> None:
        """等待指定模型包出现或消失。"""
        deadline = time.monotonic() + (
            self.timeout if timeout is None else timeout
        )
        while time.monotonic() < deadline:
            if self.has_model(model_name) is present:
                return
            time.sleep(0.2)
        state = "出现" if present else "消失"
        raise TimeoutError(f"模型包未在限定时间内{state}：{model_name}")

    def open_import_file_dialog(self) -> ModelPackageFileDialog:
        """点击“导入模型包”并返回文件选择窗口。"""
        self.import_model_package_button().click_input()
        return ModelPackageFileDialog.wait_for_open(
            self.handle,
            self.timeout,
        )

    def import_model_package(
        self,
        file_path: str | Path,
    ) -> None:
        """选择并提交一个模型包文件。"""
        self.open_import_file_dialog().select_file(file_path)

    def _model_row_items(self, model_name: str) -> list:
        """返回指定模型包所在行的全部 DataItem 控件。"""
        table = self.model_package_table().wrapper_object()
        items = [
            item
            for item in table.descendants(control_type="DataItem")
            if item.is_visible()
        ]
        column_count = len(self.table_header_names())
        if column_count == 0:
            raise RuntimeError("模型包表格没有列")
        for index in range(0, len(items), column_count):
            row = items[index:index + column_count]
            if row and row[0].window_text().strip() == model_name:
                return row
        raise RuntimeError(f"模型包表格中不存在：{model_name}")

    def open_delete_model_dialog(
        self,
        model_name: str,
    ) -> ModelPackageMessageBox:
        """点击指定模型行最右侧删除按钮并返回确认提示框。"""
        operation_cell = self._model_row_items(model_name)[-1]
        rect = operation_cell.rectangle()
        operation_cell.click_input(
            coords=(max(1, rect.width() - 25), rect.height() // 2),
        )
        return ModelPackageMessageBox.wait_for_open(
            self.handle,
            self.timeout,
        )

    def memory_usage_label(self):
        """定位显存占用率文本。"""
        labels = [
            control
            for control in self.window.descendants(control_type="Text")
            if control.is_visible()
            and control.element_info.class_name
            == "mmind::MemoryUsageLabel"
        ]
        if not labels:
            raise RuntimeError("未找到显存占用率文本")
        return labels[0]

    def print_control_identifiers(self) -> None:
        """打印窗口完整控件树。"""
        self.window.print_control_identifiers()

    def close(self) -> None:
        """通过右上角关闭按钮关闭窗口。"""
        if not self.is_visible():
            return
        hwnd = self.handle
        self.close_button().invoke()
        wait_window_hidden(hwnd, self.timeout)
