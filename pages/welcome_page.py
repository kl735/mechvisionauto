# coding: utf-8
"""Mech-Vision 欢迎首页 Page Object。"""

from __future__ import annotations

from pywinauto import Application

WELCOME_DIALOG_ID = "mmind__TypicalProjectDlg"
TITLE_BAR_PREFIX = f"{WELCOME_DIALOG_ID}.frame.titleBarWidget.normalTitleBar"
STACKED_PREFIX = f"{WELCOME_DIALOG_ID}.frame.tabWidget.qt_tabwidget_stackedwidget"
WELCOME_PREFIX = f"{STACKED_PREFIX}.mmind__WelcomeWidget"
TEMPLATE_PREFIX = f"{STACKED_PREFIX}.mmind__TemplateProjectWidget"
SIDE_PREFIX = f"{WELCOME_PREFIX}.sideWidget"
MAIN_PREFIX = f"{WELCOME_PREFIX}.mainWidget"
OPERATION_PREFIX = f"{MAIN_PREFIX}.oprationPlane"
RECENT_PREFIX = f"{MAIN_PREFIX}.recentProjectsWidget"
TEMPLATE_TITLE_PREFIX = f"{TEMPLATE_PREFIX}.titleBar"
TEMPLATE_CARD_PREFIX = f"{TEMPLATE_PREFIX}.frame_cardInfo"
TEMPLATE_DETAIL_PREFIX = f"{TEMPLATE_PREFIX}.widget_detail"


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


class SolutionLibraryPanel:
    """封装点击“从案例库新建”后切换到的案例库（mmind__TemplateProjectWidget）页面。"""

    def __init__(self, page: WelcomePage) -> None:
        self.page = page

    def root(self):
        """定位案例库页面根容器。"""
        panel = self.page._control(
            TEMPLATE_PREFIX,  # TEMPLATE_PREFIX = f"{STACKED_PREFIX}.mmind__TemplateProjectWidget"
            "Group",
        )
        panel.wait("exists visible", timeout=self.page.timeout)
        return panel

    def is_open(self) -> bool:
        """判断当前是否已切换到案例库页面。"""
        title = self.title_label()
        return title.exists(timeout=1) and title.is_visible()

    def title_label(self):
        """定位左上角“案例库”标题文本。"""
        return self.page._control(
            f"{TEMPLATE_TITLE_PREFIX}.solutionLibraryTitle",
            "Text",
            "案例库",
        )

    def back_button(self):
        """定位左上角返回欢迎首页按钮。"""
        return self.page._control(
            f"{TEMPLATE_TITLE_PREFIX}.frame.backToWelcomePage",
            "Button",
        )

    def back_to_welcome(self) -> None:
        """点击返回按钮回到欢迎首页。"""
        self.page._click(self.back_button())

    def search_edit(self):
        """定位案例库顶部搜索输入框。"""
        return self.page._control(
            f"{TEMPLATE_PREFIX}.lineEdit_search",
            "Edit",
        )

    def download_button(self):
        """定位右上角下载案例按钮。"""
        return self.page._control(
            f"{TEMPLATE_PREFIX}.pushButton_download",
            "Button",
        )

    def category_group(self):
        """定位分类标签区域（包含一级分类与动态出现的二级分类）。"""
        group = self.page._control(
            f"{TEMPLATE_CARD_PREFIX}.widget_group",
            "Group",
        )
        group.wait("exists visible", timeout=self.page.timeout)
        return group

    def category_tab(self, title: str):
        """按名称定位一级分类标签（如“应用模板”、“教学示例”、“典型案例”）。"""
        tab = self.category_group().child_window(
            title=title,
            control_type="Text",
        )
        tab.wait("exists visible", timeout=self.page.timeout)
        return tab

    def select_category(
        self,
        title: str,
        expected_subcategory: str | None = None,
    ) -> None:
        """点击切换一级分类标签，可选等待切换后出现的二级分类标签。"""
        tab = self.category_tab(title)
        self.page.main_window.set_focus()
        tab.wrapper_object().parent().click_input()
        if expected_subcategory is not None:
            expected_tab = self.category_group().child_window(
                title=expected_subcategory,
                control_type="Text",
            )
            expected_tab.wait(
                "exists visible",
                timeout=self.page.timeout,
            )

    def subcategory_tab(self, title: str):
        """按名称定位二级分类标签（如“预处理”、“3D定位”、“2D定位”等）。"""
        tab = self.category_group().child_window(
            title=title,
            control_type="Text",
        )
        tab.wait("exists visible", timeout=self.page.timeout)
        return tab

    def select_subcategory(self, title: str) -> None:
        """点击切换二级分类标签。"""
        tab = self.subcategory_tab(title)
        self.page.main_window.set_focus()
        tab.wrapper_object().parent().click_input()

    def card_list(self):
        """定位中间案例卡片 List 容器。"""
        list_view = self.page._control(
            f"{TEMPLATE_CARD_PREFIX}.listView_cards",
            "List",
        )
        list_view.wait("exists visible", timeout=self.page.timeout)
        return list_view

    def card_items(self) -> list:
        """返回当前分类下的所有案例卡片 ListItem 列表。"""
        return self.card_list().wrapper_object().descendants(
            control_type="ListItem",
        )

    def card_item(self, index: int = 0):
        """按索引获取指定的案例卡片 ListItem。"""
        items = self.card_items()
        try:
            return items[index]
        except IndexError as error:
            raise IndexError(
                f"案例卡片索引超出范围：{index}，当前卡片数量：{len(items)}"
            ) from error

    def select_card(self, index: int = 0) -> str:
        """点击选中指定索引的案例卡片，并返回底部详情区回显的方案名称。"""
        card = self.card_item(index)
        self.page.main_window.set_focus()
        card.click_input()
        return self.selected_solution_name()

    def solution_name_edit(self):
        """定位底部详情区的“方案名称”输入框。"""
        edit = self.page._control(
            f"{TEMPLATE_DETAIL_PREFIX}.lineEdit_soluName",
            "Edit",
        )
        edit.wait("exists visible", timeout=self.page.timeout)
        return edit

    def selected_solution_name(self) -> str:
        """读取当前选中案例卡片对应的方案名称。"""
        edit = self.solution_name_edit().wrapper_object()
        text = edit.window_text().strip()
        if text:
            return text
        return edit.iface_value.CurrentValue.strip()

    # def set_solution_name(self, name: str) -> None:
    #     """修改底部详情区的“方案名称”。"""
    #     edit = self.solution_name_edit()
    #     self.page.main_window.set_focus()
    #     edit.set_edit_text(name)

    def path_edit(self):
        """定位底部详情区的“路径”输入框。"""
        edit = self.page._control(
            f"{TEMPLATE_DETAIL_PREFIX}.lineEdit_path",
            "Edit",
        )
        edit.wait("exists visible", timeout=self.page.timeout)
        return edit

    def select_dir_button(self):
        """定位路径输入框右侧的选择目录按钮。"""
        return self.page._control(
            f"{TEMPLATE_DETAIL_PREFIX}.lineEdit_path.pushButton_selectDir",
            "Group",
        )

    def docs_button(self):
        """定位右下角“教程”按钮。"""
        return self.page._control(
            f"{TEMPLATE_DETAIL_PREFIX}.pushButton_docs",
            "Button",
            "教程",
        )

    def create_button(self):
        """定位右下角“创建”按钮。"""
        return self.page._control(
            f"{TEMPLATE_DETAIL_PREFIX}.pushButton_create",
            "Button",
            "创建",
        )

    # def click_create(self) -> None:
    #     """点击“创建”按钮创建当前选中的案例方案。"""
    #     self.page._click(self.create_button())


class WelcomePage:
    """封装欢迎首页上的入口、最近使用列表和帮助链接。"""

    def __init__(self, main_window, timeout: float = 60) -> None:
        self.main_window = main_window
        self.timeout = timeout
        self.recent = RecentUsePanel(self)
        self.solution_library = SolutionLibraryPanel(self)

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
        # uia_window = uia_app.window(handle=native_window.handle)
        # return cls(uia_window, timeout=timeout)

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
        control.wait(
            "exists visible enabled ready",
            timeout=self.timeout,
        )
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

    def create_from_library(self) -> SolutionLibraryPanel:
        """点击“从案例库新建”并返回案例库页面对象。"""
        button = self.create_from_library_button()
        button.wait(
            "exists visible enabled ready",
            timeout=self.timeout,
        )
        self.main_window.set_focus()
        button.invoke()
        self.solution_library.root()
        return self.solution_library

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
