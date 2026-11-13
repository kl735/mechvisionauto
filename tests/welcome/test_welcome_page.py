# coding: utf-8
"""欢迎首页中不依赖网络和外部测试数据的稳定 UI 用例。"""

import os
from pathlib import Path

from pywinauto import Application
from pywinauto.application import ProcessNotFoundError
from pywinauto.timings import wait_until

from pages.welcome_page import WelcomePage, InvalidSolutionDialog
from pages.main_window_page import MainWindowPage
from services import VisionSdkClient
from utils.mech_vision_app import EXE_PATH, wait_for_main_window
from utils.window_helper import wait_window_hidden


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
