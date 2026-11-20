# coding: utf-8
"""Mech-Vision 欢迎首页 Page Object。"""

from __future__ import annotations

import time

from pywinauto import Application
from pywinauto.mouse import click, keyboard, scroll
from pywinauto.timings import wait_until

from utils.solution_library_resources import count_online_resources
from utils.window_helper import (
    process_id_from_window,
    visible_process_windows,
    wait_window_hidden,
)

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

class InvalidSolutionDialog:
    """封装选择非方案文件夹后弹出的提示框。"""

    MESSAGE_BOX_CLASS = "mmind::StyledMessageBox"
    EXPECTED_TEXT = "无效方案文件夹"

    def __init__(self, window, timeout: float = 10) -> None:
        self.window = window
        self.timeout = timeout

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        timeout: float = 10,
    ) -> "InvalidSolutionDialog":
        """等待同一进程中的无效方案提示框出现。"""
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
                        info.class_name != cls.MESSAGE_BOX_CLASS
                        or info.name != "Mech-Vision"
                    ):
                        continue
                    dialog = cls(window, timeout)
                    if cls.EXPECTED_TEXT in dialog.message_text():
                        return dialog
                except Exception:
                    continue
            time.sleep(0.1)
        raise TimeoutError("未出现“无效方案文件夹”提示框")

    def message_text(self) -> str:
        """获取提示框中的可见文本。"""
        texts = [
            control.window_text().strip()
            for control in self.window.descendants(control_type="Text")
            if control.is_visible() and control.window_text().strip()
        ]
        return "\n".join(dict.fromkeys(texts))

    def confirm_button(self):
        """定位“确定”按钮。"""
        button = self.window.child_window(
            title="确定",
            control_type="Button",
        )
        button.wait("exists visible enabled", timeout=self.timeout)
        return button

    # def named_buttons(self) -> list[str]:
    #     """返回所有有名称的可见按钮。"""
    #     return [
    #         button.window_text().strip()
    #         for button in self.window.descendants(control_type="Button")
    #         if button.is_visible() and button.window_text().strip()
    #     ]

    def confirm(self) -> None:
        """点击“确定”并等待提示框关闭。"""
        hwnd = self.window.handle
        self.confirm_button().invoke()
        wait_window_hidden(hwnd, timeout=self.timeout)


class DownloadConfirmDialog:
    """封装案例库下载资源时的确认提示框。"""

    MESSAGE_BOX_CLASSES = {
        "mmind::StyledMessageBox",
        "#32770",
    }
    YES_TITLES = ("确定", "是(Y)", "是(&Y)", "是", "Yes", "Yes(Y)")

    def __init__(self, window, timeout: float = 10) -> None:
        self.window = window
        self.timeout = timeout

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        timeout: float = 10,
    ) -> "DownloadConfirmDialog":
        """等待同一进程中的下载确认框出现。"""
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
                    dialog = cls(window, timeout=10)
                    class_name = info.class_name or ""
                    if (
                        class_name in cls.MESSAGE_BOX_CLASSES
                        or "MessageBox" in class_name
                        or dialog.yes_button_control() is not None
                    ):
                        if dialog.yes_button_control() is not None:
                            return dialog
                except Exception:
                    continue
            time.sleep(0.1)
        raise TimeoutError("未出现案例库下载确认框")

    def yes_button_control(self):
        """定位“是”或“确定”按钮，找不到时返回 None。"""
        try:
            buttons = self.window.descendants(control_type="Button")
        except Exception:
            return None
        for button in buttons:
            title = button.window_text().strip()
            if (
                title in self.YES_TITLES
                or title.startswith("是")
                or title.lower().startswith("yes")
            ):
                return button
        return None

    def named_buttons(self) -> list[str]:
        """返回确认框中可见按钮的标题。"""
        return [
            button.window_text().strip()
            for button in self.window.descendants(control_type="Button")
            if button.is_visible() and button.window_text().strip()
        ]

    def cancel_button(self):
        """定位“取消”按钮，找不到时返回 None。"""
        try:
            buttons = self.window.descendants(control_type="Button")
        except Exception:
            return None
        for button in buttons:
            title = button.window_text().strip()
            if title in ("取消", "取消(N)", "取消(&N)", "Cancel") or title.startswith("取消"):
                return button
        return None

    def confirm(self) -> None:
        """点击“是”并等待确认框关闭。"""
        button = self.yes_button_control()
        if button is None:
            raise LookupError("下载确认框中未找到“是”按钮")
        hwnd = self.window.handle
        self.window.set_focus()
        button.invoke()
        wait_window_hidden(hwnd, timeout=self.timeout)


class LatestLibraryResourceDialog:
    """封装“当前已是最新案例库资源”提示框。"""

    MESSAGE_BOX_CLASS = "mmind::StyledMessageBox"
    EXPECTED_TEXT = "当前已是最新案例库资源"

    def __init__(self, window, timeout: float = 10) -> None:
        self.window = window
        self.timeout = timeout

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        timeout: float = 10,
    ) -> "LatestLibraryResourceDialog":
        """等待同一进程中的“已是最新资源”提示框。"""
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
                    if info.class_name != cls.MESSAGE_BOX_CLASS:
                        continue
                    dialog = cls(window, timeout)
                    if cls.EXPECTED_TEXT in dialog.message_text():
                        return dialog
                except Exception:
                    continue
            time.sleep(0.1)
        raise TimeoutError("未出现“当前已是最新案例库资源”提示框")

    def message_text(self) -> str:
        """读取提示框文本。"""
        texts = [
            control.window_text().strip()
            for control in self.window.descendants(control_type="Text")
            if control.is_visible() and control.window_text().strip()
        ]
        return "\n".join(dict.fromkeys(texts))

    def confirm_button(self):
        """定位“确定”按钮。"""
        button = self.window.child_window(
            title="确定",
            control_type="Button",
        )
        button.wait("exists visible enabled", timeout=self.timeout)
        return button

    def confirm(self) -> None:
        """点击确定并等待提示框关闭。"""
        hwnd = self.window.handle
        self.confirm_button().invoke()
        wait_window_hidden(hwnd, timeout=self.timeout)


class WelcomeFolderDialog:
    """封装欢迎页“打开方案/工程”使用的 Windows 文件夹选择框。"""

    CLASS_NAME = "#32770"

    def __init__(self, window, timeout: float = 10) -> None:
        self.window = window
        self.timeout = timeout

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        title: str,
        timeout: float = 10,
    ) -> "WelcomeFolderDialog":
        """等待与欢迎窗口同进程、标题匹配的文件夹选择框。"""
        process_id = process_id_from_window(reference_hwnd)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for hwnd in visible_process_windows(process_id):
                try:
                    app = Application(backend="uia").connect(handle=hwnd)
                    window = app.window(handle=hwnd)
                    info = window.element_info
                    if (
                        info.name == title
                        and info.class_name == cls.CLASS_NAME
                    ):
                        return cls(window, timeout)
                except Exception:
                    continue
            time.sleep(0.1)
        raise TimeoutError(f"未出现“{title}”文件夹选择窗口")

    def is_open(self) -> bool:
        """文件夹选择框当前是否可见。"""
        return self.window.exists(timeout=1) and self.window.is_visible()
    # def address_edit(self):
    #     """激活地址栏并定位地址编辑框。"""
    #     self.window.set_focus()
    #     keyboard.send_keys("%d")
    #     edit = self.window.child_window(
    #         title="地址",
    #         control_type="Edit",
    #     )
    #     edit.wait("exists visible", timeout=self.timeout)
    #     return edit

    def current_path(self) -> str:
        """读取地址栏编辑框中的完整路径。"""
        self.window.set_focus()
        keyboard.send_keys("%d")
        edit = self.window.child_window(
            title="地址",
            control_type="Edit",
        )
        edit.wait("exists visible", timeout=self.timeout)
        return edit.wrapper_object().iface_value.CurrentValue.strip()

    def cancel_button(self):
        """定位文件夹选择框中的“取消”按钮。"""
        button = self.window.child_window(
            auto_id="2",
            control_type="Button",
        )
        button.wait("exists visible enabled", timeout=self.timeout)
        return button

    def cancel(self) -> None:
        """取消选择并等待文件夹选择框关闭。"""
        hwnd = self.window.handle
        self.cancel_button().invoke()
        wait_window_hidden(hwnd, timeout=self.timeout)

    def folder_label(self):
        """定位说明当前选择类型的“文件夹:”文本。"""
        label = self.window.child_window(
            auto_id="1090",
            control_type="Text",
        )
        label.wait("exists visible", timeout=self.timeout)
        return label

    def select_folder_button(self):
        """定位“选择文件夹”按钮。"""
        button = self.window.child_window(
            auto_id="1",
            control_type="Button",
        )
        button.wait("exists visible enabled", timeout=self.timeout)
        return button

    def folder_edit(self):
        """定位底部文件夹路径输入框。"""
        edit = self.window.child_window(
            auto_id="1152",
            control_type="Edit",
        )
        edit.wait("exists visible enabled", timeout=self.timeout)
        return edit

    # def current_path(self) -> str:
    #     """读取地址栏中的当前文件夹路径。"""
    #     for control in self.window.descendants(control_type="ToolBar"):
    #         text = control.window_text().strip()
    #         prefix = "地址:"
    #         if text.startswith(prefix):
    #             return text[len(prefix):].strip()
    #     raise RuntimeError("未读取到文件夹选择框的当前路径")

    def open_folder(self, folder) -> None:
        """输入目标文件夹并点击“选择文件夹”。"""
        edit = self.folder_edit().wrapper_object()
        edit.set_edit_text(str(folder))
        hwnd = self.window.handle
        self.select_folder_button().invoke()
        wait_window_hidden(hwnd, timeout=self.timeout)


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

    def _select_switch(self, control) -> None:
        """触发按钮点击并等待最近使用类型切换完成。"""
        control.wait(
            "exists visible enabled ready",
            timeout=self.page.timeout,
        )
        self.page.main_window.set_focus()
        wrapper = control.wrapper_object()
        if bool(wrapper.is_selected()):
            return

        wrapper.invoke()
        point = wrapper.rectangle().mid_point()
        click(button="left", coords=(point.x, point.y))
        wait_until(
            timeout=5,
            retry_interval=0.1,
            func=lambda: bool(
                control.wrapper_object().is_selected()
            ),
            value=True,
        )

    def show_solutions(self) -> None:
        """切换到最近使用的方案列表。"""
        self._select_switch(self.solution_switch())

    def is_solutions_selected(self) -> bool:
        """“方案”列表当前是否处于选中状态。"""
        control = self.solution_switch()
        control.wait("exists visible", timeout=self.page.timeout)
        return bool(control.wrapper_object().is_selected())

    def project_switch(self):
        """定位“工程”切换按钮。"""
        return self.page._control(
            f"{MAIN_PREFIX}.projectSwitch",
            "RadioButton",
            "工程",
        )
    def column_headers(self) -> list[str]:
        """返回最近使用表头文字。"""
        header = self.page._control(
            f"{RECENT_PREFIX}.headerTableWidget",
            "Table",
        )
        header.wait("exists", timeout=self.page.timeout)
        return [
            item.window_text().strip()
            for item in header.descendants(control_type="DataItem")
            if item.window_text().strip()
        ]
        
    def show_projects(self) -> None:
        """切换到最近使用的工程列表。"""
        self._select_switch(self.project_switch())

    def is_projects_selected(self) -> bool:
        """“工程”列表当前是否处于选中状态。"""
        control = self.project_switch()
        control.wait("exists visible", timeout=self.page.timeout)
        return bool(control.wrapper_object().is_selected())

    def table(self):
        """定位最近使用列表下的方案/工程列表。"""
        return self.page._control(
            f"{RECENT_PREFIX}.recentUseTableWidget",
            "Table",
        )

    def table_items(self) -> list[str]:
        """返回最近使用列表下的方案/工程列表中的所有条目。"""
        table = self.table()
        table.wait("exists", timeout=self.page.timeout)
        return table.descendants(control_type="DataItem")

    def rows_items(self) -> list[list]:
        """按每 一行（3 个 DataItem） 一组封装最近使用条目。"""
        items = self.table_items()
        grouped: list[list] = []
        for index in range(0, len(items), 3):
            group = items[index:index + 3]
            if len(group) != 3:
                continue
            grouped.append(group)
        return grouped

    def titles(self) -> list[str]:
        """返回最近使用列表中的文档标题。"""
        table = self.table()
        table.wait("exists", timeout=self.page.timeout)
        items = table.descendants(control_type="DataItem")
        names = []
        for index, item in enumerate(items):
            if index % 3 != 0:
                continue
            text = item.window_text().strip()
            if text:
                names.append(text)
        return names

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
    @classmethod
    def wait_for_open(cls, reference_hwnd: int, timeout: float = 10) -> "SolutionLibraryPanel":
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
                        info.class_name != "mmind::TypicalProjectDlg"
                        or info.automation_id != "mmind__TypicalProjectDlg"
                        or info.name != "欢迎使用Mech-Vision"
                    ):
                        continue
                    library = cls(WelcomePage(window, timeout))
                    if library.is_open():
                        return library
                except Exception:
                    continue
            time.sleep(0.1)
        raise TimeoutError("未出现案例库页面")

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
        button = self.back_button()
        button.wait(
            "exists visible enabled ready",
            timeout=self.page.timeout,
        )
        button.invoke()
        self.page.create_empty_solution_button().wait(
            "exists visible",
            timeout=self.page.timeout,
        )

    def search_edit(self):
        """定位案例库顶部搜索输入框。"""
        return self.page._control(
            f"{TEMPLATE_PREFIX}.lineEdit_search",
            "Edit",
        )

    def search(self, keyword: str) -> None:
        """在案例库搜索框中输入关键字。"""
        edit = self.search_edit()
        edit.wait(
            "exists visible enabled ready",
            timeout=self.page.timeout,
        )
        self.page.main_window.set_focus()
        edit.set_edit_text(keyword)

    def clear_search(self) -> None:
        """清空案例库搜索框。"""
        self.search("")

    def download_button(self):
        """定位右上角下载案例按钮。"""
        return self.page._control(
            f"{TEMPLATE_PREFIX}.pushButton_download",
            "Button",
        )

    def click_download(self) -> None:
        """点击右上角下载按钮，不处理随后弹出的确认框。"""
        button = self.download_button()
        button.wait(
            "exists visible enabled ready",
            timeout=self.page.timeout,
        )
        self.page.main_window.set_focus()
        button.invoke()

    def wait_until_download_complete(self, timeout: float = 180) -> None:
        """等待 online 资源落地且界面出现卡片。"""
        deadline = time.monotonic() + timeout
        last_count = -1
        stable_since: float | None = None
        while time.monotonic() < deadline:
            resource_count = count_online_resources()
            try:
                card_count = len(self.card_items())
            except Exception:
                card_count = 0
            if resource_count > 0 and card_count > 0:
                if resource_count == last_count:
                    if stable_since is None:
                        stable_since = time.monotonic()
                    elif time.monotonic() - stable_since >= 2:
                        return
                else:
                    stable_since = None
                last_count = resource_count
            else:
                last_count = resource_count
                stable_since = None
            time.sleep(0.5)
        raise TimeoutError(
            f"{timeout} 秒内案例库资源未下载完成："
            f"online={count_online_resources()}，"
            f"卡片={len(self.card_items()) if self.card_list().exists(timeout=1) else 0}"
        )

    def download_online_resources(self, timeout: float = 180) -> None:
        """点击下载、确认提示，并等待资源落地且界面刷新。"""
        button = self.download_button()
        button.wait(
            "exists visible enabled ready",
            timeout=self.page.timeout,
        )
        self.page.main_window.set_focus()
        button.invoke()
        DownloadConfirmDialog.wait_for_open(
            self.page.main_window.handle,
        ).confirm()

        deadline = time.monotonic() + timeout
        last_count = -1
        stable_since: float | None = None
        while time.monotonic() < deadline:
            resource_count = count_online_resources()
            try:
                card_count = len(self.card_items())
            except Exception:
                card_count = 0
            if resource_count > 0 and card_count > 0:
                if resource_count == last_count:
                    if stable_since is None:
                        stable_since = time.monotonic()
                    elif time.monotonic() - stable_since >= 2:
                        return
                else:
                    stable_since = None
                last_count = resource_count
            else:
                last_count = resource_count
                stable_since = None
            time.sleep(0.5)
        raise TimeoutError(
            f"{timeout} 秒内案例库资源未下载完成："
            f"online={count_online_resources()}，"
            f"卡片={len(self.card_items()) if self.card_list().exists(timeout=1) else 0}"
        )
    

    # def _fully_visible_card_items(self) -> list:
    #     items = self.card_items()
    #     if not items:
    #         return []
    #     list_rect = self.card_list().wrapper_object().rectangle()
    #     full_height = max(item.rectangle().height() for item in items)
    #     visible = []
    #     for item in items:
    #         rect = item.rectangle()
    #         if rect.top < list_rect.top - 1:
    #             continue
    #         if rect.bottom > list_rect.bottom + 1:
    #             continue
    #         if full_height and rect.height() < full_height * 0.9:
    #             continue
    #         visible.append(item)
    #     return visible or items[:1]

    # def _select_card_control(self, card, previous: str = "") -> str:
    #     self.page.main_window.set_focus()
    #     card.click_input()
    #     return self._wait_solution_name(previous, timeout=3)

    # def _wait_solution_name(self, previous: str, timeout: float) -> str:
    #     deadline = time.monotonic() + timeout
    #     current = previous
    #     while time.monotonic() < deadline:
    #         try:
    #             current = self.selected_solution_name()
    #         except Exception:
    #             current = previous
    #         if current and (not previous or current != previous):
    #             return current
    #         time.sleep(0.1)
    #     try:
    #         return self.selected_solution_name() or previous
    #     except Exception:
    #         return previous

    # def _wheel_card_list(self, down: bool, card=None) -> None:
    #     target = card or (self._fully_visible_card_items() or [None])[-1]
    #     if target is None:
    #         return
    #     rect = target.rectangle()
    #     scroll(
    #         coords=(
    #             (rect.left + rect.right) // 2,
    #             (rect.top + rect.bottom) // 2,
    #         ),
    #         wheel_dist=-4 if down else 4,
    #     )
    #     time.sleep(0.2)

    def tab_titles(self) -> list[str]:
        """当前分类栏中可见的一级，按界面顺序去重。"""
        titles: list[str] = []
        seen: set[str] = set()
        for control in self.category_group().wrapper_object().descendants(
            control_type="Text",
        ):
            try:
                if not control.is_visible():
                    continue
            except Exception:
                continue
            text = (control.window_text() or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            titles.append(text)
        return titles

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

    def has_subcategory(self, title: str) -> bool:
        """当前分类区域是否出现指定二级分类。"""
        return self.category_group().child_window(
            title=title,
            control_type="Text",
        ).exists(timeout=1)

    def is_application_templates_selected(self) -> bool:
        """当前是否停留在“应用模板”一级分类。"""
        tab = self.category_tab("应用模板")
        wrapper = tab.wrapper_object()
        parent = wrapper.parent()
        try:
            if bool(parent.is_selected()):
                return True
        except Exception:
            pass
        return (
            tab.is_visible()
            and not self.has_subcategory("预处理")
            and not self.has_subcategory("有序工件拣选")
        )

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
        items = []
        for child in self.card_list().wrapper_object().children():
            if child.element_info.control_type == "ListItem":
                items.append(child)
        if items:
            return items

        return self.card_list().wrapper_object().descendants(
            control_type="ListItem",
        )
    def card_names(self) -> list[str]:
        """读出当前分类下全部方案名称。"""
        items = self.card_items()
        if not items:
            return []

        item = items[0]
        rect = item.rectangle()
        item.click_input(
            coords=(rect.width() // 2, rect.height() // 2),
        )

        first_name = self.selected_solution_name()
        if not first_name:
            return []

        names = [first_name]
        while len(names) < 200:
            previous = names[-1]
            keyboard.send_keys("{DOWN}", vk_packet=False)

            current = previous
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                current = self.selected_solution_name()
                if current and current != previous:
                    break
                time.sleep(0.1)

            if not current or current == previous:
                break
            names.append(current)

        return names


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
        previous = ""
        try:
            previous = self.selected_solution_name()
        except Exception:
            pass
        card = self.card_item(index)
        self.page.main_window.set_focus()
        card.click_input()
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            current = self.selected_solution_name()
            if current and (index == 0 or current != previous):
                return current
            time.sleep(0.2)
        return self.selected_solution_name()

    def select_card_by_name(self, name: str) -> str:
        """按方案名称选中案例卡片，并确认底部详情区回显一致。"""
        # bring_window_to_front(self.page.main_window.handle)
        self.page.main_window.set_focus()
        count = len(self.card_items())
        seen_names: list[str] = []
        for index in range(count):
            current = self.select_card(index)
            if current and current not in seen_names:
                seen_names.append(current)
            if current == name:
                return current

        raise LookupError(
            f"案例库中未找到方案“{name}”，"
            f"卡片数量：{count}，底部方案名：{seen_names}"
        )

    def open_docs(self) -> None:
        """点击右下角“教程”按钮，不负责等待外部浏览器。"""
        button = self.docs_button()
        button.wait(
            "exists visible enabled ready",
            timeout=self.page.timeout,
        )
        self.page.main_window.set_focus()
        button.click_input()

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
    def close(self):
        """点击 closeWidgetBtn 关闭当前窗口。"""
        button = self.page._control(
            f"{WELCOME_DIALOG_ID}.frame.titleBarWidget.closeWidgetBtn",
            "Button",
        )
        button.wait(
            "exists visible enabled ready",
        )
        button.invoke()



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

    def user_manual_button(self):
        """定位“用户手册”入口。"""
        return self._control(f"{SIDE_PREFIX}.helpWidget", "Group")

    def open_user_manual(self) -> None:
        """点击“用户手册”。"""
        self._click(self.user_manual_button())

    def community_button(self):
        """定位“在线社区”入口。"""
        return self._control(f"{SIDE_PREFIX}.widget_community", "Group")

    def open_community(self) -> None:
        """点击“在线社区”。"""
        self._click(self.community_button())

    def versionTip_text(self) -> str:
        """读取版本号，只保留三段数字（如 2.2.2）。"""
        text = self.version_text().strip()
        if not text:
            return ""
        return text.split("-", 1)[0].strip()


    def close_button(self):
        """定位首页右上角关闭按钮。"""
        return self._control(
            f"{TITLE_BAR_PREFIX}.exitBtn",
            "Button",
        )

    def close(self) -> None:
        """关闭欢迎首页。"""
        button = self.close_button()
        button.wait(
            "exists visible enabled ready",
            timeout=self.timeout,
        )
        button.invoke()

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

    def open_solution_dialog(self) -> WelcomeFolderDialog:
        """打开并返回“打开方案”文件夹选择框。"""
        button = self.open_solution_button()
        button.wait(
            "exists visible enabled ready",
            timeout=self.timeout,
        )
        button.invoke()
        return WelcomeFolderDialog.wait_for_open(
            self.main_window.handle,
            "打开方案",
            timeout=self.timeout,
        )

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

    def open_project_dialog(self) -> WelcomeFolderDialog:
        """打开并返回“打开工程”文件夹选择框。"""
        button = self.open_project_button()
        button.wait(
            "exists visible enabled ready",
            timeout=self.timeout,
        )
        button.invoke()
        return WelcomeFolderDialog.wait_for_open(
            self.main_window.handle,
            "打开工程",
            timeout=self.timeout,
        )

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
        button = self.create_empty_solution_button()
        button.wait(
            "exists visible enabled ready",
            timeout=self.timeout,
        )
        button.invoke()

    def _side_button(self, auto_id: str, title: str):
        return self._control(
            f"{SIDE_PREFIX}.{auto_id}",
            "Button",
            title,
        )

    def whats_new_button(self):
        """定位“有什么新功能？”入口。"""
        return self._side_button("whatIsNew", "有什么新功能？")

    def open_whats_new(self) -> None:
        """点击“有什么新功能？”。"""
        self._click(self.whats_new_button())

    def introduction_button(self):
        """定位“Mech-Vision简介”入口。"""
        return self._side_button("knownVisionQuickly", "Mech-Vision简介")

    def open_introduction(self) -> None:
        """点击“Mech-Vision简介”。"""
        self._click(self.introduction_button())

    def getting_started_button(self):
        """定位“快速入门”入口。"""
        return self._side_button("gettingStart", "快速入门")

    def open_getting_started(self) -> None:
        """点击“快速入门”。"""
        self._click(self.getting_started_button())

    def step_guide_button(self):
        """定位“步骤参考指南”入口。"""
        return self._side_button("stepUserGuide", "步骤参考指南")

    def open_step_guide(self) -> None:
        """点击“步骤参考指南”。"""
        self._click(self.step_guide_button())

    def video_tutorials_button(self):
        """定位“视频教程”入口。"""
        return self._side_button("pushButton_video", "视频教程")

    def open_video_tutorials(self) -> None:
        """点击“视频教程”。"""
        self._click(self.video_tutorials_button())

    def qa_feedback_button(self):
        """定位“问答反馈”入口。"""
        return self._side_button("pushButton_QA", "问答反馈")

    def open_qa_feedback(self) -> None:
        """点击“问答反馈”。"""
        self._click(self.qa_feedback_button())
