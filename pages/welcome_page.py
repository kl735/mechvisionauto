# coding: utf-8
"""Mech-Vision 欢迎首页 Page Object。"""

from __future__ import annotations

from pywinauto import Application

WELCOME_DIALOG_ID = "mmind__TypicalProjectDlg"
TITLE_BAR_PREFIX = f"{WELCOME_DIALOG_ID}.frame.titleBarWidget.normalTitleBar"
WELCOME_PREFIX = (
    f"{WELCOME_DIALOG_ID}.frame.tabWidget.qt_tabwidget_stackedwidget."
    "mmind__WelcomeWidget"
)
SIDE_PREFIX = f"{WELCOME_PREFIX}.sideWidget"
MAIN_PREFIX = f"{WELCOME_PREFIX}.mainWidget"
OPERATION_PREFIX = f"{MAIN_PREFIX}.oprationPlane"
RECENT_PREFIX = f"{MAIN_PREFIX}.recentProjectsWidget"


class RecentUsePanel:
    """封装首页“最近使用”区域的切换、定位和打开操作。"""

    def __init__(self, page: WelcomePage) -> None:
        self.page = page

    def solution_switch(self):
        """定位“方案”切换按钮。"""
        return self.page._control(
            f"{MAIN_PREFIX}.solutionSwitch",
            "RadioButton",
            "方案",
        )

    def show_solutions(self) -> None:
        """切换到最近使用的方案列表。"""
        self.page._click(self.solution_switch())

    def project_switch(self):
        """定位“工程”切换按钮。"""
        return self.page._control(
            f"{MAIN_PREFIX}.projectSwitch",
            "RadioButton",
            "工程",
        )

    def show_projects(self) -> None:
        """切换到最近使用的工程列表。"""
        self.page._click(self.project_switch())

    def table(self):
        """定位最近使用列表。"""
        return self.page._control(
            f"{RECENT_PREFIX}.recentUseTableWidget",
            "Table",
        )

    def item(self, name: str, found_index: int = 0):
        """按名称定位最近使用条目。"""
        table = self.table()
        table.wait("exists", timeout=self.page.timeout)
        return table.child_window(
            title=name,
            control_type="DataItem",
            found_index=found_index,
        )

    def open(self, name: str, found_index: int = 0) -> None:
        """双击打开指定的最近使用条目。"""
        item = self.item(name, found_index)
        item.wait("exists", timeout=self.page.timeout)
        item.double_click_input()


class WelcomePage:
    """封装欢迎首页上的入口、最近使用列表和帮助链接。"""

    def __init__(self, main_window, timeout: float = 60) -> None:
        self.main_window = main_window
        self.timeout = timeout
        self.recent = RecentUsePanel(self)

    @classmethod
    def attach(cls, app, timeout: float = 30) -> "WelcomePage":
        """用 Win32 定位欢迎窗口，再通过句柄连接 UIA。"""
        if app is None:
            raise RuntimeError("Mech-Vision 尚未启动")

        native_window = app.window(
            title="欢迎使用Mech-Vision",
        )
        native_window.wait(
            "exists visible",
            timeout=timeout,
            retry_interval=0.1,
        )
        uia_app = Application(backend="uia").connect(handle=native_window.handle)
        return cls(uia_app.window(handle=native_window.handle), timeout=timeout)

    def exists(self, timeout: float = 5) -> bool:
        """欢迎首页是否存在。"""
        return self.create_empty_solution_button().exists(timeout=timeout)

    def _control(
        self,
        auto_id: str,
        control_type: str,
        title: str | None = None,
    ):
        criteria = {
            "auto_id": auto_id,
            "control_type": control_type,
        }
        if title is not None:
            criteria["title"] = title
        return self.main_window.child_window(**criteria)

    def _click(self, control) -> None:
        """等待控件存在后点击。"""
        control.wait("exists", timeout=self.timeout)
        self.main_window.set_focus()
        control.click_input()

    def close_button(self):
        """定位首页右上角关闭按钮。"""
        return self._control(
            f"{TITLE_BAR_PREFIX}.exitBtn",
            "Button",
        )

    def close(self) -> None:
        """关闭欢迎首页。"""
        self._click(self.close_button())

    def version_text(self) -> str:
        """读取 Mech-Vision 版本号。"""
        control = self._control(f"{SIDE_PREFIX}.versionTip", "Text")
        control.wait("exists", timeout=self.timeout)
        return control.window_text()

    def version_date(self) -> str:
        """读取版本发布日期。"""
        control = self._control(f"{SIDE_PREFIX}.versionDate", "Text")
        control.wait("exists", timeout=self.timeout)
        return control.window_text()

    def open_solution_button(self):
        """定位“打开方案”按钮。"""
        return self._control(
            f"{OPERATION_PREFIX}.openSolution",
            "Button",
            "打开方案",
        )

    def open_solution(self) -> None:
        """点击“打开方案”，不处理后续文件选择框。"""
        self._click(self.open_solution_button())

    def open_project_button(self):
        """定位“打开工程”按钮。"""
        return self._control(
            f"{OPERATION_PREFIX}.openProject",
            "Button",
            "打开工程",
        )

    def open_project(self) -> None:
        """点击“打开工程”，不处理后续文件选择框。"""
        self._click(self.open_project_button())

    def create_from_library_button(self):
        """定位“从案例库新建”按钮。"""
        return self._control(
            f"{OPERATION_PREFIX}.createFromSolutionLibrary",
            "Button",
            "从案例库新建",
        )

    def create_from_library(self) -> None:
        """点击“从案例库新建”。"""
        self._click(self.create_from_library_button())

    def create_empty_solution_button(self):
        """定位“新建空白方案”按钮。"""
        return self._control(
            f"{OPERATION_PREFIX}.createEmptySolution",
            "Button",
            "新建空白方案",
        )

    def create_empty_solution(self) -> None:
        """点击“新建空白方案”。"""
        self._click(self.create_empty_solution_button())

    def _side_button(self, auto_id: str, title: str):
        return self._control(
            f"{SIDE_PREFIX}.{auto_id}",
            "Button",
            title,
        )

    def open_whats_new(self) -> None:
        """点击“有什么新功能？”。"""
        self._click(self._side_button("whatIsNew", "有什么新功能？"))

    def open_introduction(self) -> None:
        """点击“Mech-Vision简介”。"""
        self._click(
            self._side_button("knownVisionQuickly", "Mech-Vision简介"),
        )

    def open_getting_started(self) -> None:
        """点击“快速入门”。"""
        self._click(self._side_button("gettingStart", "快速入门"))

    def open_step_guide(self) -> None:
        """点击“步骤参考指南”。"""
        self._click(self._side_button("stepUserGuide", "步骤参考指南"))

    def open_video_tutorials(self) -> None:
        """点击“视频教程”。"""
        self._click(self._side_button("pushButton_video", "视频教程"))

    def open_qa_feedback(self) -> None:
        """点击“问答反馈”。"""
        self._click(self._side_button("pushButton_QA", "问答反馈"))
