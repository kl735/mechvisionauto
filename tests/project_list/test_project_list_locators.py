# coding: utf-8
"""验证 ProjectListPage、右键菜单与删除确认框的控件定位能力。"""

import shutil
from pathlib import Path

from pages.main_window_page import MainWindowPage
from services import VisionSdkClient
from tests.project_list.conftest import (
    SOLUTION_NAME,
    SOLUTION_PATH,
    wait_for_project_created,
    wait_for_project_deleted,
    wait_for_solution_loaded,
)


def test_project_list_page_locators(
    main_page: MainWindowPage,
) -> None:
    """打开指定方案并验证工程列表及右键菜单定位方法。"""
    assert SOLUTION_PATH.is_dir(), f"测试方案不存在：{SOLUTION_PATH}"

    with VisionSdkClient() as sdk:
        sdk.open_solution(SOLUTION_PATH)
        wait_for_solution_loaded(main_page)

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


def test_create_and_delete_project_dialog_workflow(
    main_page: MainWindowPage,
    tmp_path: Path,
) -> None:
    """验证新建工程 -> 删除确认弹窗取消 -> 删除确认弹窗确认。"""
    assert SOLUTION_PATH.is_dir(), f"测试方案不存在：{SOLUTION_PATH}"
    solution_copy = tmp_path / SOLUTION_NAME
    shutil.copytree(SOLUTION_PATH, solution_copy)

    with VisionSdkClient() as sdk:
        sdk.open_solution(solution_copy)
        wait_for_solution_loaded(main_page)

        project_list = main_page.project_list
        project_list.open_solution_menu(SOLUTION_NAME).click_item("新建工程")
        wait_for_project_created(main_page, "工程3")

        dialog = project_list.open_delete_project_dialog("工程3")
        assert "确定删除所选工程" in dialog.message_text()
        assert dialog.delete_button().exists()
        assert dialog.cancel_button().exists()
        dialog.cancel()
        assert "工程3" in project_list.project_names()

        dialog = project_list.open_delete_project_dialog("工程3")
        dialog.confirm_delete()
        wait_for_project_deleted(main_page, "工程3")
        assert "工程3" not in project_list.project_names()
