# coding: utf-8
"""“Python包管理工具”窗口 Page Object。"""

from __future__ import annotations

import time

from pywinauto import Application

from utils.window_helper import (
    process_id_from_window,
    visible_process_windows,
    wait_window_hidden,
)


class PythonPackageManagerPage:
    """封装从工具箱打开的“Python包管理工具”窗口。"""

    TITLE = "Python包管理工具"
    CLASS_NAME = "mmind::PyPackageManagementDialog"
    AUTOMATION_ID = "mmind__Dialog"
    CONTROL_TYPE = "Window"
    EDITOR_ID = (
        "mmind__Dialog.dialogFrame.contentWidget."
        "mmind__PyPackageEditor"
    )
    MAIN_ID = f"{EDITOR_ID}.mainWidget"
    TOP_ID = f"{MAIN_ID}.topWidget"
    LEFT_ID = f"{MAIN_ID}.leftWidget"
    RIGHT_ID = f"{MAIN_ID}.rightWidget"
    TOOL_ID = f"{RIGHT_ID}.toolWidget"

    def __init__(self, window, timeout: float = 10) -> None:
        self.window = window
        self.timeout = timeout
        self._validate_window()

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        timeout: float = 10,
    ) -> "PythonPackageManagerPage":
        """等待同一进程中的 Python 包管理工具窗口出现。"""
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

        raise TimeoutError(f"未出现窗口：{cls.TITLE}")

    def _validate_window(self) -> None:
        """确认传入窗口是 Python 包管理工具窗口。"""
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
                "传入窗口不是 Python 包管理工具窗口："
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

    def focus(self) -> None:
        """使用 Win32 句柄将窗口置于前台。"""
        Application(backend="win32").connect(
            handle=self.handle,
        ).window(handle=self.handle).set_focus()

    def print_control_identifiers(self) -> None:
        """打印 Python 包管理工具窗口控件树。"""
        self.window.print_control_identifiers()

    def _control(
        self,
        auto_id: str,
        control_type: str | None = None,
    ):
        """按 AutomationId 定位并等待页面内部控件。"""
        criteria = {"auto_id": auto_id}
        if control_type is not None:
            criteria["control_type"] = control_type
        control = self.window.child_window(**criteria)
        control.wait(
            "exists visible",
            timeout=self.timeout,
        )
        return control

    def close_button(self):
        """定位右上角关闭按钮。"""
        return self._control(
            "mmind__Dialog.dialogFrame.titleBarWidget.closeBtn",
            "Button",
        )

    def python_interpreter_label(self):
        """定位“Python解释器”文本。"""
        return self._control(
            f"{self.TOP_ID}.interpreterLabel",
            "Text",
        )

    def interpreter_combo_box(self):
        """定位 Python 解释器下拉框。"""
        return self._control(
            f"{self.TOP_ID}.interpreterComboBox",
            "ComboBox",
        )

    def copy_path_button(self):
        """定位“复制”解释器路径按钮。"""
        return self._control(
            f"{self.TOP_ID}.copyPathPushButton",
            "Button",
        )

    def installed_packages_label(self):
        """定位“已安装的Python包”文本。"""
        return self._control(
            f"{self.LEFT_ID}.installedPackageLabel",
            "Text",
        )

    def installed_packages_table(self):
        """定位已安装 Python 包表格。"""
        return self._control(
            f"{self.LEFT_ID}.installedPackageTable",
            "Table",
        )

    def installed_table_headers(self) -> list[str]:
        """返回已安装包表格的列标题。"""
        table = self.installed_packages_table().wrapper_object()
        return [
            control.window_text().strip()
            for control in table.descendants(control_type="Header")
            if control.is_visible() and control.window_text().strip()
        ]

    def import_button(self):
        """定位“导入”按钮。"""
        return self._control(
            f"{self.LEFT_ID}.importPushButton",
            "Button",
        )

    def export_button(self):
        """定位“导出”按钮。"""
        return self._control(
            f"{self.LEFT_ID}.exportPushButton",
            "Button",
        )

    def available_packages_label(self):
        """定位“可安装的Python包”文本。"""
        return self._control(
            f"{self.RIGHT_ID}.findPackageLabel",
            "Text",
        )

    def package_name_edit(self):
        """定位 Python 包名称搜索输入框。"""
        return self._control(
            f"{self.RIGHT_ID}.packageNameLineEdit",
            "Edit",
        )

    def search_button(self):
        """定位“查找”按钮。"""
        return self._control(
            f"{self.RIGHT_ID}.searchPushButton",
            "Button",
        )

    def no_content_label(self):
        """定位无搜索结果时显示的“暂无可用”文本。"""
        return self._control(
            f"{self.RIGHT_ID}.stackedWidget.page1.noContentLabel",
            "Text",
        )

    def specify_source_checkbox(self):
        """定位“指定下载源”开关。"""
        return self._control(
            f"{self.TOOL_ID}.specifySourceCheckBox",
            "CheckBox",
        )

    def source_combo_box(self):
        """定位下载源下拉框。"""
        return self._control(
            f"{self.TOOL_ID}.sourceCombox",
            "ComboBox",
        )

    def install_button(self):
        """定位“安装”按钮。"""
        return self._control(
            f"{self.TOOL_ID}.installButton",
            "Button",
        )

    def close(self) -> None:
        """关闭窗口并等待其隐藏。"""
        if not self.is_visible():
            return
        hwnd = self.handle
        self.close_button().invoke()
        wait_window_hidden(hwnd, self.timeout)
