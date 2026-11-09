# coding: utf-8
"""验证 ProjectListPage、右键菜单与删除确认框的控件定位及确认/取消操作能力。"""

from pages.main_window_page import MainWindowPage
from services import VisionSdkClient
from tests.project_list.conftest import (
    SOLUTION_NAME,
    wait_for_project_created,
    wait_for_project_deleted,
)


def test_project_list_page_locators(
    main_page: MainWindowPage,
    solution_sdk: VisionSdkClient,
) -> None:
    """打开指定方案并验证工程列表及右键菜单定位方法。"""
    _ = solution_sdk
    project_list = main_page.project_list
    assert project_list.dock().exists()
    assert project_list.tree().exists()
    assert project_list.title_bar().exists()
    assert project_list.title_label().window_text() == "工程列表"

    title_buttons = project_list.title_buttons()
    assert len(title_buttons) >= 2, "工程列表标题栏按钮少于两个"
    assert project_list.left_title_button() == title_buttons[0]
    assert project_list.right_title_button() == title_buttons[-1]

    named_items = project_list.tree_items(named_only=True)
    names = [item.window_text().strip() for item in named_items]
    print(f"工程树节点：{names}")
    assert SOLUTION_NAME in names
    assert "工程1" in names
    assert "工程2" in names

    assert project_list.item(SOLUTION_NAME).exists()
    assert project_list.item("1").exists()
    assert project_list.item("工程1").exists()
    assert project_list.locate("工程1").exists()

    project_list.select("工程1")
    selected_project = project_list.locate("工程1")
    assert selected_project.is_visible()
    assert selected_project.is_enabled()

    solution_menu = project_list.open_solution_menu(SOLUTION_NAME)
    try:
        assert solution_menu.element_info.class_name == "QMenu"
        assert solution_menu.close_solution_item().exists()
        assert solution_menu.open_solution_folder_item().exists()
        assert solution_menu.create_project_item().exists()
        assert solution_menu.autoload_solution_item().exists()
        assert solution_menu.rename_solution_item().exists()
        assert solution_menu.manage_permission_item().exists()
        assert solution_menu.backup_solution_item().exists()
        assert solution_menu.reset_project_id_item().exists()
    finally:
        solution_menu.close()

    project_menu = project_list.open_project_menu("工程1")
    try:
        assert project_menu.element_info.class_name == "QMenu"
        assert project_menu.close_project_item().exists()
        assert project_menu.open_project_folder_item().exists()
        assert project_menu.rename_project_item().exists()
        assert project_menu.delete_project_item().exists()
        assert project_menu.copy_project_item().exists()
        assert project_menu.backup_solution_item().exists()
    finally:
        project_menu.close()


def test_cancel_delete_project_dialog(
    main_page: MainWindowPage,
    solution_sdk: VisionSdkClient,
) -> None:
    """新建工程3后打开删除确认弹窗，验证点击“取消”不删除工程。"""
    _ = solution_sdk
    project_list = main_page.project_list
    for extra in [
        name
        for name in project_list.project_names()
        if name not in ("工程1", "工程2")
    ]:
        project_list.open_delete_project_dialog(extra).confirm_delete()
        wait_for_project_deleted(main_page, extra)

    project_list.open_solution_menu(SOLUTION_NAME).click_item("新建工程")
    wait_for_project_created(main_page, "工程3")

    dialog = project_list.open_delete_project_dialog("工程3")
    assert "确定删除所选工程" in dialog.message_text()
    assert dialog.delete_button().exists()
    assert dialog.cancel_button().exists()
    dialog.cancel()

    assert "工程3" in project_list.project_names()
    assert len(project_list.project_names()) == 3


def test_rename_project(
    main_page: MainWindowPage,
    solution_sdk: VisionSdkClient,
) -> None:
    """将已新建的工程3重命名为工程3_重命名，验证工程树和 SDK 中的工程名称修改成功。"""
    project_list = main_page.project_list
    assert "工程3" in project_list.project_names()

    renamed_project = "工程3_重命名"
    project_list.rename_project("工程3", renamed_project)
    wait_for_project_created(main_page, renamed_project)

    current_names = project_list.project_names()
    sdk_names = [proj.name for proj in solution_sdk.get_projects()]
    print(f"重命名后工程列表：UI={current_names}, SDK={sdk_names}")
    assert renamed_project in current_names
    assert "工程3" not in current_names
    assert renamed_project in sdk_names


def test_confirm_delete_project_dialog(
    main_page: MainWindowPage,
    solution_sdk: VisionSdkClient,
) -> None:
    """对重命名后的工程打开删除确认弹窗，验证点击“删除”成功删除工程。"""
    _ = solution_sdk
    project_list = main_page.project_list
    target_project = "工程3_重命名"
    assert target_project in project_list.project_names()

    dialog = project_list.open_delete_project_dialog(target_project)
    assert "确定删除所选工程" in dialog.message_text()
    dialog.confirm_delete()
    wait_for_project_deleted(main_page, target_project)

    assert target_project not in project_list.project_names()
    assert len(project_list.project_names()) == 2
