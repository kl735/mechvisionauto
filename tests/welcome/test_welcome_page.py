# coding: utf-8
"""欢迎首页中不依赖网络和外部测试数据的稳定 UI 用例。"""

import os
import time
from pathlib import Path
from turtle import title

import pytest
import win32gui
import yaml
from pywinauto import Application
from pywinauto.application import ProcessNotFoundError
from pywinauto.mouse import click
from pywinauto.timings import wait_until

from pages.welcome_page import (
    WelcomePage,
    InvalidSolutionDialog,
    SolutionLibraryPanel,
    DownloadConfirmDialog,
    LatestLibraryResourceDialog,
)
from pages.main_window_page import MainWindowPage
from services import VisionSdkClient
from utils.browser_helper import urls_match, wait_for_docs_url
from utils.mech_vision_app import EXE_PATH, wait_for_main_window
from utils.solution_library_resources import (
    LIBRARY_GROUP_PATH,
    add_library_subgroup,
    clear_online_resources,
    count_online_resources,
    library_categories,
    online_category_catalog,
    rename_library_group,
    rename_library_subgroup,
    remove_library_group,
    remove_library_subgroup,
    remove_online_card,
)
from utils.window_helper import wait_window_hidden

SOLUTION_LIBRARY_DOCS = Path(__file__).with_name("solution_library_docs.yaml")


TEST_VIS_FILE = Path(
    "C:/Users/mech-mind/AppData/Local/Temp/pytest-of-mech-mind/"
    "pytest-80/ai_classification_solution0/solution/工程1/工程1.vis"
)
TEST_PROJECT_NAME = r"工程1"

TEST_SOLUTION_DIR = r"C:\Users\mech-mind\AppData\Local\Temp\pytest-of-mech-mind\pytest-80\ai_classification_solution0\solution"

TEST_SOLUTION_PATH = r"C:\Users\mech-mind\Desktop\MechvisionAuto"

TEST_NOT_SOLUTION_DIR_PATH = r"E:\工具"

def _assert_visible_enabled(control, name: str, timeout: float) -> None:
    """验证指定欢迎页控件存在、可见且可用。"""
    control.wait("exists visible enabled", timeout=timeout)
    assert control.is_visible(), f"{name}不可见"
    assert control.is_enabled(), f"{name}不可用"


def test_welcome_page_displays_core_information_and_actions(
    welcome_page: WelcomePage,
) -> None:
    """验证欢迎页基础信息和四个主要操作入口。"""
    assert welcome_page.exists(timeout=5), "欢迎页面未显示"
    assert welcome_page.version_text().strip(), "未读取到软件版本号"
    assert welcome_page.version_date().strip(), "未读取到版本发布日期"

    controls = {
        "关闭": welcome_page.close_button(),
        "打开方案": welcome_page.open_solution_button(),
        "打开工程": welcome_page.open_project_button(),
        "从案例库新建": welcome_page.create_from_library_button(),
        "新建空白方案": welcome_page.create_empty_solution_button(),
    }
    for name, control in controls.items():
        _assert_visible_enabled(control, name, welcome_page.timeout)


def test_welcome_page_displays_help_entries(
    welcome_page: WelcomePage,
) -> None:
    """验证欢迎页左侧帮助入口均可被 UIA 稳定定位。"""
    controls = {
        "有什么新功能？": welcome_page.whats_new_button(),
        "Mech-Vision简介": welcome_page.introduction_button(),
        "快速入门": welcome_page.getting_started_button(),
        "步骤参考指南": welcome_page.step_guide_button(),
        "视频教程": welcome_page.video_tutorials_button(),
        "问答反馈": welcome_page.qa_feedback_button(),
    }
    for name, control in controls.items():
        _assert_visible_enabled(control, name, welcome_page.timeout)


def test_VIS_018789(
    welcome_page: WelcomePage,
) -> None:
    """验证新建空白方案后进入主界面，并生成一个不含 Step 的工程。"""
    welcome_handle = welcome_page.main_window.handle

    welcome_page.create_empty_solution()

    wait_window_hidden(welcome_handle, timeout=30)
    main_handle = wait_for_main_window(timeout=60)
    main_page = MainWindowPage.attach(main_handle, timeout=60)

    assert main_page.exists(timeout=5), "新建空白方案后主窗口未显示"

    project_list = main_page.project_list
    project_names = wait_until(
        timeout=30,
        retry_interval=0.2,
        func=project_list.project_names,
        value=1,
        op=lambda names, count: len(names) == count,
    )

    solution_name = project_list.solution_name()
    assert solution_name == "新建方案"
    project_name = project_list.project_names()
    assert project_name == ["工程1"]

    with VisionSdkClient() as sdk:
        projects = sdk.get_projects()
        sdk_project_names = [project.name for project in projects]

        assert sdk_project_names == project_names
        assert sdk.get_step_names(project_names[0]) == []

def test_VIS_018782(
    welcome_page: WelcomePage,
    mech_app,
) -> None:
    """验证关闭欢迎窗口后 Mech-Vision 进程正常退出。"""
    assert mech_app.app is not None
    assert mech_app.app.is_process_running(), "Mech-Vision 进程未运行"

    welcome_page.close()

    wait_until(
        timeout=10,
        retry_interval=0.2,
        func=lambda: not mech_app.app.is_process_running(),
        value=True,
    )
    assert not mech_app.app.is_process_running(), "Mech-Vision 进程未退出"


def test_recent_use_can_switch_between_solution_and_project(
    welcome_page: WelcomePage,
) -> None:
    """验证“最近使用”区域可在方案和工程列表间切换。"""
    _assert_visible_enabled(
        welcome_page.recent.solution_switch(),
        "最近使用-方案",
        welcome_page.timeout,
    )
    _assert_visible_enabled(
        welcome_page.recent.project_switch(),
        "最近使用-工程",
        welcome_page.timeout,
    )
    _assert_visible_enabled(
        welcome_page.recent.table(),
        "最近使用列表",
        welcome_page.timeout,
    )

    try:
        welcome_page.recent.show_projects()
        wait_until(
            timeout=5,
            retry_interval=0.2,
            func=welcome_page.recent.is_projects_selected,
            value=True,
        )

        welcome_page.recent.show_solutions()
        wait_until(
            timeout=5,
            retry_interval=0.2,
            func=welcome_page.recent.is_solutions_selected,
            value=True,
        )
    finally:
        if not welcome_page.recent.is_solutions_selected():
            welcome_page.recent.show_solutions()


def test_VIS_018788(
    welcome_page: WelcomePage,
) -> None:
    """验证从欢迎页进入案例库界面"""
    library = welcome_page.create_from_library()
    try:
        assert library.is_open(), "案例库页面未打开"
        assert library.title_label().window_text() == "案例库"
        assert library.search_edit().is_visible(), "案例库搜索框不可见"
        assert library.download_button().is_visible(), "案例资源下载按钮不可见"
        assert library.card_list().is_visible(), "案例卡片列表不可见"
    finally:
        if library.is_open():
            library.back_to_welcome()


def test_open_solution_dialog_can_be_cancelled(
    welcome_page: WelcomePage,
) -> None:
    """验证“打开方案”文件夹选择框能够打开并取消。"""
    dialog = welcome_page.open_solution_dialog()
    try:
        assert dialog.is_open(), "“打开方案”文件夹选择框未显示"
        _assert_visible_enabled(
            dialog.cancel_button(),
            "打开方案-取消",
            welcome_page.timeout,
        )
    finally:
        if dialog.is_open():
            dialog.cancel()

    assert welcome_page.exists(timeout=5), "取消后未返回欢迎页面"


def test_open_project_dialog_can_be_cancelled(
    welcome_page: WelcomePage,
) -> None:
    """验证“打开工程”文件夹选择框能够打开并取消。"""
    dialog = welcome_page.open_project_dialog()
    try:
        assert dialog.is_open(), "“打开工程”文件夹选择框未显示"
        _assert_visible_enabled(
            dialog.cancel_button(),
            "打开工程-取消",
            welcome_page.timeout,
        )
    finally:
        if dialog.is_open():
            dialog.cancel()

    assert welcome_page.exists(timeout=5), "取消后未返回欢迎页面"


def test_solution_library_defaults_to_application_templates(
    welcome_page: WelcomePage,
) -> None:
    """进入案例库后，默认选中一级分类“应用模板”。"""
    library = welcome_page.create_from_library()
    try:
        assert library.is_open(), "案例库页面未打开"
        assert library.category_tab("应用模板").is_visible(), "未找到一级分类“应用模板”"
        assert library.is_application_templates_selected(), (
            "进入案例库后默认未选中“应用模板”"
        )
    finally:
        if library.is_open():
            library.back_to_welcome()


@pytest.fixture
def empty_online_resources():
    """软件启动前清空案例库 online 资源。"""
    clear_online_resources()
    yield


@pytest.fixture
def welcome_page_empty_library(
    empty_online_resources,
    welcome_page: WelcomePage,
) -> WelcomePage:
    """提供已清空 online 后再启动的欢迎页。"""
    return welcome_page


def _split_tab_titles(
    titles: list[str],
    primary_names: list[str],
) -> tuple[list[str], list[str]]:
    primary_set = set(primary_names)
    primary = [title for title in titles if title in primary_set]
    secondary = [title for title in titles if title not in primary_set]
    return primary, secondary


def _assert_library_cards(
    library: SolutionLibraryPanel,
    expected: list[str],
    label: str,
) -> None:
    if expected:
        wait_until(
            timeout=10,
            retry_interval=0.3,
            func=lambda: bool(library.card_items()),
            value=True,
        )
        wait_until(
            timeout=10,
            retry_interval=0.3,
            func=lambda: library.select_card(0),
            value=expected[0],
        )
    else:
        wait_until(
            timeout=10,
            retry_interval=0.3,
            func=lambda: len(library.card_items()),
            value=0,
        )
    # actual = library.card_names()
    # assert actual == expected, (
    #     f"{label} 界面与 online 不一致：界面={actual}，online={expected}"
    # )


@pytest.mark.solution_library_download
def test_solution_library_download_matches_online_application_templates(
    welcome_page_empty_library: WelcomePage,
) -> None:
    """清空 online 后下载资源，一级/二级分类和卡片应与磁盘资源一致。"""
    welcome_page = welcome_page_empty_library
    library = welcome_page.create_from_library()
    try:
        assert library.is_open(), "案例库页面未打开"
        assert library.is_application_templates_selected(), (
            "进入案例库后默认未选中“应用模板”"
        )
        assert count_online_resources() == 0, "清空后 online 仍有资源"
        assert len(library.card_items()) == 0, "清空后应用模板仍有卡片"

        library.click_download()
        dialog = DownloadConfirmDialog.wait_for_open(
            library.page.main_window.handle,
        )
        buttons = dialog.named_buttons()
        assert "确定" in buttons, f"下载确认框没有“确定”按钮：{buttons}"
        assert "取消" in buttons, f"下载确认框没有“取消”按钮：{buttons}"
        ok_button = dialog.yes_button_control()
        cancel_button = dialog.cancel_button()
        assert ok_button is not None and ok_button.is_enabled(), "“确定”按钮不可用"
        assert (
            cancel_button is not None and cancel_button.is_enabled()
        ), "“取消”按钮不可用"
        dialog.confirm()
        library.wait_until_download_complete(timeout=300)

        catalog = online_category_catalog()
        assert catalog, "下载完成后 online 中没有可用分类"
        primary_names = [category["name"] for category in catalog]
        actual_primary, _ = _split_tab_titles(library.tab_titles(), primary_names)
        assert actual_primary == primary_names, (
            "一级分类与 library_group 不一致："
            f"界面={actual_primary}，期望={primary_names}"
        )

        for category in catalog:
            expected_subs = [sub["name"] for sub in category["subgroups"]]
            library.select_category(
                category["name"],
                expected_subcategory=expected_subs[0] if expected_subs else None,
            )
            actual_primary, actual_subs = _split_tab_titles(
                library.tab_titles(),
                primary_names,
            )
            assert actual_primary == primary_names, (
                f"切换到“{category['name']}”后一级分类变化："
                f"界面={actual_primary}，期望={primary_names}"
            )
            assert actual_subs == expected_subs, (
                f"“{category['name']}”二级分类与 online 不一致："
                f"界面={actual_subs}，期望={expected_subs}"
            )

            if not category["subgroups"]:
                _assert_library_cards(
                    library,
                    category["cards"],
                    category["name"],
                )
                continue

            for sub in category["subgroups"]:
                library.select_subcategory(sub["name"])
                _assert_library_cards(
                    library,
                    sub["cards"],
                    f"{category['name']}/{sub['name']}",
                )
    finally:
        if library.is_open():
            library.back_to_welcome()


def _application_template_docs() -> list[tuple[str, str]]:
    docs = yaml.safe_load(SOLUTION_LIBRARY_DOCS.read_text(encoding="utf-8"))
    return list(docs["application_templates"].items())


APPLICATION_TEMPLATE_DOCS = _application_template_docs()


# ids=... 只影响报告上的名字，函数里用不到。
@pytest.mark.parametrize(
    "name, expected_url",
    APPLICATION_TEMPLATE_DOCS,
    ids=[name for name, _ in APPLICATION_TEMPLATE_DOCS],
)
def test_solution_library_application_template_docs_can_open(
    welcome_page: WelcomePage,
    name: str,
    expected_url: str,
) -> None:
    """打开指定应用模板教程，并校验跳转 URL。"""
    library = welcome_page.create_from_library()
    try:
        assert library.is_open(), "案例库页面未打开"
        assert library.is_application_templates_selected(), (
            "进入案例库后默认未选中“应用模板”"
        )
        library.page.main_window.set_focus()
        selected = library.select_card_by_name(name)
        assert selected == name, f"选中方案名不匹配：{selected} != {name}"
        library.open_docs()
        _, _, actual_url = wait_for_docs_url(expected_url)
        assert urls_match(actual_url, expected_url), (
            f"方案“{name}”教程 URL 不匹配："
            f"实际={actual_url}，期望={expected_url}"
        )
    finally:
        library.page.main_window.set_focus()
        if library.is_open():
            library.back_to_welcome()



def test_solution_library_displays_primary_categories(
    welcome_page: WelcomePage,
) -> None:
    """验证案例库三个一级分类均可稳定定位。"""
    library = welcome_page.create_from_library()
    try:
        for category in ("应用模板", "教学示例", "典型案例"):
            control = library.category_tab(category)
            control.wait("exists visible", timeout=welcome_page.timeout)
            assert control.is_visible(), f"案例库一级分类不可见：{category}"
    finally:
        if library.is_open():
            library.back_to_welcome()


def test_solution_library_search_can_filter_and_restore_cards(
    welcome_page: WelcomePage,
) -> None:
    """验证案例库搜索可以过滤卡片，清空后恢复原列表。"""
    library = welcome_page.create_from_library()
    search = library.search_edit()
    original_count = len(library.card_items())
    assert original_count > 0, "案例库没有可用于搜索验证的本地卡片"

    try:
        search.set_edit_text("__automation_no_matching_case__")
        wait_until(
            timeout=5,
            retry_interval=0.2,
            func=lambda: len(library.card_items()),
            value=0,
        )

        search.set_edit_text("")
        wait_until(
            timeout=5,
            retry_interval=0.2,
            func=lambda: len(library.card_items()),
            value=original_count,
        )
    finally:
        if search.exists(timeout=1):
            search.set_edit_text("")
        if library.is_open():
            library.back_to_welcome()


def test_VIS_018781() -> None:
    """打开工程文件并验证主窗口、工程列表和工程编辑区。"""
    assert TEST_VIS_FILE.is_file(), f"测试工程不存在：{TEST_VIS_FILE}"

    native_app: Application | None = None
    try:
        os.startfile(str(TEST_VIS_FILE))

        main_handle = wait_for_main_window(timeout=60)
        native_app = Application(backend="win32").connect(
            handle=main_handle,
        )

        welcome_windows = native_app.windows(
            title="欢迎使用Mech-Vision",
            top_level_only=True,
        )
        assert not any(
            window.is_visible() for window in welcome_windows
        ), "打开工程后仍显示欢迎窗口"

        main_page = MainWindowPage.attach(
            main_handle,
            timeout=60,
        )
        assert main_page.exists(timeout=5), "Mech-Vision 主窗口未显示"

        wait_until(
            timeout=30,
            retry_interval=0.2,
            func=lambda: (
                TEST_PROJECT_NAME
                in main_page.project_list.project_names()
            ),
            value=True,
        )
        assert TEST_PROJECT_NAME in main_page.project_list.project_names()

        canvas = main_page.project_editor.canvas()
        canvas.wait("exists visible", timeout=30)
        assert canvas.is_visible(), "工程编辑区未显示"
    finally:
        if native_app is None:
            try:
                native_app = Application(backend="win32").connect(
                    path=str(EXE_PATH),
                    timeout=2,
                )
            except ProcessNotFoundError:
                pass
        if native_app is not None and native_app.is_process_running():
            native_app.kill()


def _normalize_dialog_path(path: str) -> str:
    """统一路径分隔符，并忽略 UIA 地址栏省略的 &。"""
    return (
        path.replace("&", "")
        .replace("/", "\\")
        .rstrip("\\")
        .casefold()
    )

def test_VIS_018783(
    welcome_page: WelcomePage,
) -> None:
    """验证打开方案文件夹后关闭欢迎窗口并进入对应主界面。"""
    welcome_handle = welcome_page.main_window.handle
    open_dialog = welcome_page.open_solution_dialog()
    try:
        assert open_dialog.is_open(), "“打开方案”文件夹选择框未显示"
        # # 截图
        # open_dialog.window.capture_as_image().save("open_dialog.png")
        print(f"当前路径: {open_dialog.current_path()}")
        assert open_dialog.current_path() == TEST_SOLUTION_PATH
        # 输入要打开方案的路径，点击打开文件夹
        open_dialog.folder_edit().set_edit_text(TEST_SOLUTION_DIR)
        open_dialog.select_folder_button().click()

        assert wait_window_hidden(welcome_handle, timeout=30)


        main_handle = wait_for_main_window(timeout=60)
        main_page = MainWindowPage.attach(main_handle, timeout=60)
        assert main_page.exists(timeout=5), "打开方案后主窗口未显示"
        assert main_page.project_list.solution_name() == "solution"
        assert "工程1" in main_page.project_list.project_names()
        with VisionSdkClient() as sdk:
            current_project_all_steps = sdk.get_step_names("工程1")
            assert sorted(current_project_all_steps) == sorted([
                "2D智能相机_1",
                "AI分类（正反/有无）_1",
            ])
    finally:
        pass


def test_VIS_018784_and_VIS_018786(
    welcome_page: WelcomePage,
) -> None:
    """验证打开方案文件夹后，选择非“方案”格式的文件夹，点击弹窗中的“确定”按钮，再次点击“打开方案”按钮"""
    welcome_handle = welcome_page.main_window.handle
    open_dialog = welcome_page.open_solution_dialog()
    try:
        assert open_dialog.is_open(), "“打开方案”文件夹选择框未显示"
      
        # 输入非方案格式文件夹路径，点击确定
        open_dialog.folder_edit().set_edit_text(TEST_NOT_SOLUTION_DIR_PATH)
        open_dialog.select_folder_button().click()

        invalid_solution_dialog = InvalidSolutionDialog.wait_for_open(welcome_handle, timeout=30)
        invalid_solution_dialog.confirm()

        # 3. 提示框关闭后回到欢迎页
        assert welcome_page.exists(timeout=10), "提示关闭后未返回欢迎页面"
        # 4. 再次打开方案，默认路径为上次选择的文件夹
        second_dialog = welcome_page.open_solution_dialog()
        assert second_dialog.is_open(), "再次点击后“打开方案”窗口未显示"
        assert second_dialog.current_path() == TEST_NOT_SOLUTION_DIR_PATH
        assert second_dialog.select_folder_button().window_text() == "选择文件夹"
                
    finally:
        pass


def test_VIS_018802(
    welcome_page: WelcomePage,
    mech_app,
) -> None:
    """验证进入案例库后点击关闭按钮，Mech-Vision 进程退出。"""
    assert mech_app.app is not None
    assert mech_app.app.is_process_running(), "Mech-Vision 进程未运行"

    library = welcome_page.create_from_library()
    assert library.is_open(), "案例库页面未打开"

    welcome_page.close()

    wait_until(
        timeout=10,
        retry_interval=0.2,
        func=lambda: not mech_app.app.is_process_running(),
        value=True,
    )
    assert not mech_app.app.is_process_running(), "Mech-Vision 进程未退出"



def test_VIS_018803(
    welcome_page: WelcomePage,
    mech_app,
) -> None:
    """验证进入案例库后点击返回按钮，返回欢迎页（目前只判断是否返回欢迎页面）。"""
    assert mech_app.app is not None
    assert mech_app.app.is_process_running(), "Mech-Vision 进程未运行"

    library = welcome_page.create_from_library()
    assert library.is_open(), "案例库页面未打开"

    library.back_to_welcome()

    assert welcome_page.exists(timeout=10), "点击返回后未回到欢迎页面"
    assert not library.is_open(), "返回后案例库页面仍然打开"


def test_VIS_018790_and_VIS_018791(
    welcome_page: WelcomePage,
) -> None:
    """存在最近使用过的工程和方案的情况下，切换“最近使用”的“方案”和“工程”列表，查看表头是否正确。"""
    # 欢迎页默认选中方案列表
    assert welcome_page.recent.is_solutions_selected(), "方案列表未选中"
    assert welcome_page.recent.column_headers() == ["名称", "最近修改", "打开文件夹"]
    # 切换到工程列表
    welcome_page.recent.show_projects()
    wait_until(
        timeout=5,
        retry_interval=0.2,
        func=welcome_page.recent.column_headers,
        value=["名称", "版本号", "最近修改", "打开文件夹"],
    )

    # 切换回方案列表
    welcome_page.recent.show_solutions()
    wait_until(
        timeout=5,
        retry_interval=0.2,
        func=welcome_page.recent.column_headers,
        value=["名称", "最近修改", "打开文件夹"],
    )


def test_VIS_018805(
    main_page: MainWindowPage,
) -> None:
    """验证从主窗口点击“从案例库新建”后进入案例库。"""
    main_handle = main_page.handle
    button = main_page.create_from_library_button()
    assert button.window_text() == "从案例库新建"
    point = button.rectangle().mid_point()
    click(coords=(point.x, point.y))
    # 来判断是否出现案例库页面
    library = SolutionLibraryPanel.wait_for_open(main_handle)
    assert library.is_open(), "案例库页面未打开"
    library_hwnd = library.page.main_window.handle
    library.close()
    assert wait_window_hidden(library_hwnd, timeout=10), "关闭案例库后未关闭案例库页面"
    assert main_page.exists(timeout=5), "关闭案例库后未返回主窗口"


NO_MATCH_KEYWORD = "__automation_no_matching_case__"


def _assert_search_hit(
    library: SolutionLibraryPanel,
    keyword: str,
    label: str,
) -> None:
    library.search(keyword)
    wait_until(
        timeout=5,
        retry_interval=0.2,
        func=lambda: bool(library.card_items()),
        value=True,
    )
    selected = library.select_card(0)
    assert selected, f"{label} 搜索“{keyword}”后没有卡片"
    assert keyword in selected, (
        f"{label} 搜索未命中原案例：关键字={keyword}，选中={selected}"
    )
    # actual = library.card_names()
    # assert actual, f"{label} 搜索“{keyword}”后没有卡片"
    # assert keyword in actual, (
    #     f"{label} 搜索未命中原案例：关键字={keyword}，界面={actual}"
    # )
    # assert all(keyword in name for name in actual), (
    #     f"{label} 搜索结果包含不匹配案例：关键字={keyword}，界面={actual}"
    # )


def _assert_search_miss(library: SolutionLibraryPanel, label: str) -> None:
    library.search(NO_MATCH_KEYWORD)
    wait_until(
        timeout=5,
        retry_interval=0.2,
        func=lambda: len(library.card_items()),
        value=0,
    )
    assert len(library.card_items()) == 0, f"{label} 无匹配搜索后仍有卡片"


def _search_current_group(
    library: SolutionLibraryPanel,
    names: list[str],
    label: str,
) -> None:
    if not names:
        return
    library.clear_search()
    wait_until(
        timeout=5,
        retry_interval=0.2,
        func=lambda: bool(library.card_items()),
        value=True,
    )
    _assert_search_hit(library, names[-1], label)
    _assert_search_miss(library, label)


def test_VIS_018830(welcome_page: WelcomePage) -> None:
    """验证案例库按分类/分组搜索可命中案例，无匹配时列表为空。"""
    library = welcome_page.create_from_library()
    try:
        assert library.is_open(), "案例库页面未打开"
        catalog = online_category_catalog()
        assert catalog, "本地 online 中没有可用于搜索的分类"

        for category in catalog:
            sampled_subs = [
                sub for sub in category["subgroups"] if sub["cards"]
            ][:2]
            library.select_category(
                category["name"],
                expected_subcategory=(
                    sampled_subs[0]["name"] if sampled_subs else None
                ),
            )
            if not sampled_subs:
                _search_current_group(library, category["cards"], category["name"])
                continue
            for sub in sampled_subs:
                library.select_subcategory(sub["name"])
                _search_current_group(
                    library,
                    sub["cards"],
                    f"{category['name']}/{sub['name']}",
                )
    finally:
        try:
            library.clear_search()
        except Exception:
            pass
        if library.is_open():
            library.back_to_welcome()



def test_solution_library_set_focus_can_steal_foreground(
    welcome_page: WelcomePage,
) -> None:
    """点教程让浏览器抢前台后，验证 set_focus 能否把案例库抢回来。"""
    library = welcome_page.create_from_library()
    hwnd = library.page.main_window.handle
    try:
        assert library.is_open(), "案例库页面未打开"
        library.select_card(0)
        library.open_docs()
        wait_until(
            timeout=10,
            retry_interval=0.2,
            func=lambda: win32gui.GetForegroundWindow() != hwnd,
        )
        foreground_before = win32gui.GetForegroundWindow()
        assert foreground_before != hwnd, (
            "浏览器未抢到前台，无法验证 set_focus："
            f"前台={foreground_before}，标题={win32gui.GetWindowText(foreground_before)!r}"
        )

        library.page.main_window.set_focus()

        foreground_after = win32gui.GetForegroundWindow()
        assert foreground_after == hwnd, (
            "set_focus 未能把案例库抢回前台："
            f"前台={foreground_after}，"
            f"标题={win32gui.GetWindowText(foreground_after)!r}，"
            f"期望={hwnd}"
        )
    finally:
        if library.is_open():
            library.back_to_welcome()


HELP_OPEN_METHODS = {
    "有什么新功能？": "open_whats_new",
    "用户手册": "open_user_manual",
    "Mech-Vision简介": "open_introduction",
    "快速入门": "open_getting_started",
    "步骤参考指南": "open_step_guide",
    "视频教程": "open_video_tutorials",
    "问答反馈": "open_qa_feedback",
    "在线社区": "open_community",
}


def _help_links() -> list[tuple[str, str]]:
    docs = yaml.safe_load(SOLUTION_LIBRARY_DOCS.read_text(encoding="utf-8"))
    return list(docs["help_links"].items())


HELP_LINKS = _help_links()

# ids=... 只影响报告上的名字，函数里用不到。
@pytest.mark.parametrize(
    "name, url_template",
    HELP_LINKS,
    ids=[name for name, _ in HELP_LINKS],
)
def test_VIS_018796(
    welcome_page: WelcomePage,
    name: str,
    url_template: str,
) -> None:
    """联网情况下，文档相关链接跳转测试。"""
    assert welcome_page.exists(timeout=10), "欢迎页面未显示"
    version = welcome_page.versionTip_text()
    assert version, "未读取到软件版本号"

    open_method = HELP_OPEN_METHODS.get(name)
    assert open_method, f"未配置入口“{name}”的打开方法"

    expected_url = url_template.format(version=version)
    print(f"正在点击首页入口：{name}，期望跳转：{expected_url}")
    getattr(welcome_page, open_method)()
    _, _, actual_url = wait_for_docs_url(expected_url)
    assert urls_match(actual_url, expected_url), (
        f"入口“{name}”URL 不匹配：实际={actual_url}，期望={expected_url}"
    )
   

def test_VIS_018792(
    welcome_page: WelcomePage,
) -> None:
   pass


def test_VIS_018794(
    welcome_page: WelcomePage,
) -> None:
    pass


ORDERED_LOADING_CARD = "有序工件上料"
@pytest.fixture
def without_ordered_loading_card():
    """软件启动前删除应用模板中的有序工件上料。"""
    remove_online_card(ORDERED_LOADING_CARD)
    yield


@pytest.fixture
def welcome_page_without_ordered_loading(
    without_ordered_loading_card,
    welcome_page: WelcomePage,
) -> WelcomePage:
    """提供已删除有序工件上料后再启动的欢迎页。"""
    return welcome_page


def test_welcome_page_without_ordered_loading(
    welcome_page_without_ordered_loading: WelcomePage,
) -> None:
    """验证后台删除案例分组（有序工件上料）后，下载案例库资源后能够正确新增案例。"""
    library = welcome_page_without_ordered_loading.create_from_library()
    assert library.is_open(), "案例库页面未打开"
    assert library.is_application_templates_selected(), "默认不是应用模板标签页"
    before_names = library.card_names()
    print(f"before_names: {before_names}")
    library.click_download()
    dialog = DownloadConfirmDialog.wait_for_open(
        library.page.main_window.handle,
        )
    buttons = dialog.named_buttons()
    assert "确定" in buttons, f"下载确认框没有“确定”按钮：{buttons}"
    assert "取消" in buttons, f"下载确认框没有“取消”按钮：{buttons}"
    dialog.confirm()

    after_names = library.card_names()
    print(f"after_names: {after_names}")
    new_names = set(after_names) - set(before_names)
    print(f"下载后新增方案：{sorted(new_names)}")

    assert new_names, "下载后没有新增任何方案"


REMOVED_LIBRARY_GROUP = "教学示例"


@pytest.fixture
def without_library_group():
    """启动软件前删除案例分组，用例结束后恢复原始分组文件。"""
    original = LIBRARY_GROUP_PATH.read_bytes()
    removed = remove_library_group(REMOVED_LIBRARY_GROUP)
    assert removed is not None, f"library_group.json 中没有分组：{REMOVED_LIBRARY_GROUP}"
    try:
        yield
    finally:
        LIBRARY_GROUP_PATH.write_bytes(original)


@pytest.fixture
def welcome_page_without_library_group(
    without_library_group,
    welcome_page: WelcomePage,
) -> WelcomePage:
    """提供删除案例分组后启动的欢迎页。"""
    return welcome_page


@pytest.mark.solution_library_download
def test_download_does_not_restore_deleted_library_group(
    welcome_page_without_library_group: WelcomePage,
) -> None:
    """删除 group 字段中的案例分组后，下载资源不能恢复该分组。"""
    library = welcome_page_without_library_group.create_from_library()
    try:
        assert REMOVED_LIBRARY_GROUP not in library.tab_titles(), (
            f"删除后界面仍显示案例分组：{REMOVED_LIBRARY_GROUP}"
        )

        library.click_download()
        dialog = DownloadConfirmDialog.wait_for_open(
            library.page.main_window.handle,
        )
        dialog.confirm()
        library.wait_until_download_complete(timeout=300)

        assert REMOVED_LIBRARY_GROUP not in library.tab_titles(), (
            f"下载资源后错误恢复了案例分组：{REMOVED_LIBRARY_GROUP}"
        )
    finally:
        if library.is_open():
            library.back_to_welcome()



# def test_VIS_018824(
# ) -> None:
#     """同时删除卡片和分组后，下载只恢复卡片、不恢复分组。"""
    

RENAMED_LIBRARY_GROUP = "新的分组名称"


@pytest.fixture
def renamed_library_group():
    """启动软件前重命名教学示例，用例结束后恢复原文件。"""
    original = LIBRARY_GROUP_PATH.read_bytes()
    renamed = rename_library_group(
        REMOVED_LIBRARY_GROUP,
        RENAMED_LIBRARY_GROUP,
    )
    assert renamed, f"没有找到分组：{REMOVED_LIBRARY_GROUP}"

    local_group_names = [
        category["name"]
        for category in library_categories()
    ]
    assert RENAMED_LIBRARY_GROUP in local_group_names, (
        f"本地分组名称修改失败：{local_group_names}"
    )
    assert REMOVED_LIBRARY_GROUP not in local_group_names, (
        f"本地仍存在旧分组名称：{local_group_names}"
    )
    try:
        yield
    finally:
        LIBRARY_GROUP_PATH.write_bytes(original)


def test_VIS_018825(
    renamed_library_group,
    welcome_page: WelcomePage,
) -> None:
    """验证软件启动前修改的案例分组名称会显示在案例库中。"""
    library = welcome_page.create_from_library()
    library.click_download()
    dialog = DownloadConfirmDialog.wait_for_open(
        library.page.main_window.handle,
        )
    buttons = dialog.named_buttons()
    assert "确定" in buttons, f"下载确认框没有“确定”按钮：{buttons}"
    assert "取消" in buttons, f"下载确认框没有“取消”按钮：{buttons}"
    dialog.confirm()
    try:
        titles = library.tab_titles()
        print(f"titles: {titles}")
        assert RENAMED_LIBRARY_GROUP in titles, (
            f"案例库未显示新分组名称：{RENAMED_LIBRARY_GROUP}；实际={titles}"
        )
        assert REMOVED_LIBRARY_GROUP not in titles, (
            f"案例库仍显示旧分组名称：{REMOVED_LIBRARY_GROUP}"                                     
        )
    finally:
        if library.is_open():
            library.back_to_welcome()


SUBGROUP_PARENT = "教学示例"
ORIGINAL_LIBRARY_SUBGROUP = "预处理"
RENAMED_LIBRARY_SUBGROUP = "新的子分组名称"


@pytest.fixture
def renamed_library_subgroup():
    """启动软件前重命名教学示例子分组，用例结束后恢复原文件。"""
    original = LIBRARY_GROUP_PATH.read_bytes()
    renamed = rename_library_subgroup(
        SUBGROUP_PARENT,
        ORIGINAL_LIBRARY_SUBGROUP,
        RENAMED_LIBRARY_SUBGROUP,
    )
    assert renamed, (
        f"没有找到子分组："
        f"{SUBGROUP_PARENT}/{ORIGINAL_LIBRARY_SUBGROUP}"
    )

    category = next(
        (
            item
            for item in library_categories()
            if item["name"] == SUBGROUP_PARENT
        ),
        None,
    )
    assert category is not None, f"没有找到一级分组：{SUBGROUP_PARENT}"
    subgroup_names = [
        subgroup["name"]
        for subgroup in category["subgroups"]
    ]
    assert RENAMED_LIBRARY_SUBGROUP in subgroup_names, (
        f"本地子分组名称修改失败：{subgroup_names}"
    )
    assert ORIGINAL_LIBRARY_SUBGROUP not in subgroup_names, (
        f"本地仍存在原子分组名称：{subgroup_names}"
    )
    try:
        yield
    finally:
        LIBRARY_GROUP_PATH.write_bytes(original)



def test_VIS_018828(
    renamed_library_subgroup,
    welcome_page: WelcomePage,
) -> None:
    """验证下载资源不会覆盖修改后的子分组，其他分组显示正常。"""
    library = welcome_page.create_from_library()
    try:
        library.click_download()
        dialog = DownloadConfirmDialog.wait_for_open(
            library.page.main_window.handle,
        )
        buttons = dialog.named_buttons()
        assert "确定" in buttons, f"下载确认框没有“确定”按钮：{buttons}"
        assert "取消" in buttons, f"下载确认框没有“取消”按钮：{buttons}"
        dialog.confirm()
        try:
            latest_dialog = LatestLibraryResourceDialog.wait_for_open(
                library.page.main_window.handle,
                timeout=5,
            )
        except TimeoutError:
            library.wait_until_download_complete(timeout=300)
        else:
            assert (
                LatestLibraryResourceDialog.EXPECTED_TEXT
                in latest_dialog.message_text()
            )
            latest_dialog.confirm()

        library.select_category(
            SUBGROUP_PARENT,
            expected_subcategory=RENAMED_LIBRARY_SUBGROUP,
        )
        assert library.has_subcategory(RENAMED_LIBRARY_SUBGROUP), (
            f"未显示修改后的子分组：{RENAMED_LIBRARY_SUBGROUP}"
        )
        assert not library.has_subcategory(ORIGINAL_LIBRARY_SUBGROUP), (
            f"仍显示原子分组名称：{ORIGINAL_LIBRARY_SUBGROUP}"
        )

        library.select_category(
            "典型案例",
            expected_subcategory="有序工件拣选",
        )
        for subgroup in (
            "有序工件拣选",
            "无序工件拣选",
            "定位装配",
            "拆码垛",
            "其他",
        ):
            assert library.has_subcategory(subgroup), (
                f"典型案例缺少子分组：{subgroup}"
            )

        library.select_category(
            SUBGROUP_PARENT,
            expected_subcategory=RENAMED_LIBRARY_SUBGROUP,
        )
        assert library.has_subcategory(RENAMED_LIBRARY_SUBGROUP), (
            "切换分组后修改的子分组名称未保留"
        )
    finally:
        if library.is_open():
            library.back_to_welcome()
    

ADDED_SUBGROUP_PARENT = "教学示例"
ADDED_LIBRARY_SUBGROUP = "自动化新增子分组"


@pytest.fixture
def added_library_subgroup():
    """启动软件前新增教学示例子分组，用例结束后恢复原文件。"""
    original = LIBRARY_GROUP_PATH.read_bytes()
    subgroup_id = add_library_subgroup(
        ADDED_SUBGROUP_PARENT,
        ADDED_LIBRARY_SUBGROUP,
    )
    assert subgroup_id is not None, (
        f"新增失败或子分组已存在："
        f"{ADDED_SUBGROUP_PARENT}/{ADDED_LIBRARY_SUBGROUP}"
    )

    category = next(
        (
            item
            for item in library_categories()
            if item["name"] == ADDED_SUBGROUP_PARENT
        ),
        None,
    )
    assert category is not None, (
        f"没有找到一级分组：{ADDED_SUBGROUP_PARENT}"
    )
    subgroup_names = [
        subgroup["name"]
        for subgroup in category["subgroups"]
    ]
    assert ADDED_LIBRARY_SUBGROUP in subgroup_names, (
        f"本地未写入新增子分组：{subgroup_names}"
    )
    try:
        yield subgroup_id
    finally:
        LIBRARY_GROUP_PATH.write_bytes(original)


def test_VIS_018826(
    added_library_subgroup,
    welcome_page: WelcomePage,
) -> None:
    """验证教学示例新增子分组后下载资源仍保留该子分组。"""
    library = welcome_page.create_from_library()
    try:
        library.click_download()
        dialog = DownloadConfirmDialog.wait_for_open(
            library.page.main_window.handle,
        )
        dialog.confirm()
        try:
            latest_dialog = LatestLibraryResourceDialog.wait_for_open(
                library.page.main_window.handle,
                timeout=5,
            )
        except TimeoutError:
            library.wait_until_download_complete(timeout=300)
        else:
            latest_dialog.confirm()

        library.select_category(
            ADDED_SUBGROUP_PARENT,
            expected_subcategory=ADDED_LIBRARY_SUBGROUP,
        )
        assert library.has_subcategory(ADDED_LIBRARY_SUBGROUP), (
            f"教学示例未显示新增子分组：{ADDED_LIBRARY_SUBGROUP}"
        )
    finally:
        if library.is_open():
            library.back_to_welcome()


REMOVED_SUBGROUP_PARENT = "教学示例"
REMOVED_LIBRARY_SUBGROUP = "预处理"


@pytest.fixture
def removed_library_subgroup():
    """启动软件前删除教学示例子分组，用例结束后恢复原文件。"""
    original = LIBRARY_GROUP_PATH.read_bytes()
    removed = remove_library_subgroup(
        REMOVED_SUBGROUP_PARENT,
        REMOVED_LIBRARY_SUBGROUP,
    )
    assert removed is not None, (
        f"没有找到子分组："
        f"{REMOVED_SUBGROUP_PARENT}/{REMOVED_LIBRARY_SUBGROUP}"
    )

    category = next(
        (
            item
            for item in library_categories()
            if item["name"] == REMOVED_SUBGROUP_PARENT
        ),
        None,
    )
    assert category is not None, (
        f"没有找到一级分组：{REMOVED_SUBGROUP_PARENT}"
    )
    subgroup_names = [
        subgroup["name"]
        for subgroup in category["subgroups"]
    ]
    assert REMOVED_LIBRARY_SUBGROUP not in subgroup_names, (
        f"本地仍存在已删除子分组：{subgroup_names}"
    )
    try:
        yield removed
    finally:
        LIBRARY_GROUP_PATH.write_bytes(original)


def test_VIS_018827(
    removed_library_subgroup,
    welcome_page: WelcomePage,
) -> None:
    """验证删除教学示例子分组后，下载资源不会恢复该子分组。"""
    library = welcome_page.create_from_library()
    try:
        library.click_download()
        dialog = DownloadConfirmDialog.wait_for_open(
            library.page.main_window.handle,
        )
        dialog.confirm()
        try:
            latest_dialog = LatestLibraryResourceDialog.wait_for_open(
                library.page.main_window.handle,
                timeout=5,
            )
        except TimeoutError:
            library.wait_until_download_complete(timeout=300)
        else:
            latest_dialog.confirm()

        library.select_category(
            REMOVED_SUBGROUP_PARENT,
            expected_subcategory="3D定位",
        )
        assert not library.has_subcategory(REMOVED_LIBRARY_SUBGROUP), (
            f"下载后错误恢复了子分组：{REMOVED_LIBRARY_SUBGROUP}"
        )
        for subgroup in (
            "3D定位",
            "2D定位",
            "深度学习",
            "3D位姿调整",
            "路径规划",
            "防错过滤",
            "逻辑判断",
            "功能",
            "其他",
        ):
            assert library.has_subcategory(subgroup), (
                f"教学示例缺少其他子分组：{subgroup}"
            )
    finally:
        if library.is_open():
            library.back_to_welcome()
    