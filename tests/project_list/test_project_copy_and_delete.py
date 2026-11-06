# coding: utf-8
"""工程列表业务流测试：
1. 复制工程1/工程2的 Step 到新建工程3/工程4；
2. 分别用右键菜单和 Delete 键两种方式删除工程3/工程4中的 Step；
3. 删除工程3/工程4。
"""

import time

from pywinauto import keyboard

from pages.main_window_page import MainWindowPage
from services import VisionSdkClient
from tests.project_list.conftest import (
    PROJECT_COPY_PAIRS,
    copy_all_steps_to_new_project,
    delete_project_step_by_context_menu,
    delete_project_steps_by_delete_key,
    wait_for_project_deleted,
)


def test_01_copy_project1_and_project2_steps_to_new_projects(
    main_page: MainWindowPage,
    solution_sdk: VisionSdkClient,
) -> None:
    """用例1：依次将工程1复制到新建的工程3、工程2复制到新建的工程4，并校验 Step 一致。"""
    for source_project, target_project in PROJECT_COPY_PAIRS:
        copy_all_steps_to_new_project(
            solution_sdk,
            main_page,
            source_project,
            target_project,
        )

    assert main_page.project_list.project_names() == [
        "工程1",
        "工程2",
        "工程3",
        "工程4",
    ]
    main_page.focus()
    solution_sdk.save_solution()


def test_02_delete_steps_by_two_methods_in_project3_and_project4(
    main_page: MainWindowPage,
    solution_sdk: VisionSdkClient,
) -> None:
    """用例2：在工程3用右键菜单删除 Step，在工程4用 Delete 键删除 Step，并用 SDK 校验。"""
    delete_project_step_by_context_menu(
        solution_sdk,
        main_page,
        "工程3",
    )
    assert solution_sdk.get_step_names("工程3") == []

    delete_project_steps_by_delete_key(
        solution_sdk,
        main_page,
        "工程4",
    )
    assert solution_sdk.get_step_names("工程4") == []


def test_03_delete_created_project3_and_project4(
    main_page: MainWindowPage,
    solution_sdk: VisionSdkClient,
) -> None:
    """用例3：紧接着删除新建的工程3和工程4，并校验只剩工程1和工程2。"""
    project_list = main_page.project_list
    assert "工程3" in project_list.project_names()
    assert "工程4" in project_list.project_names()

    for target_project in ("工程3", "工程4"):
        dialog = project_list.open_delete_project_dialog(target_project)
        assert "确定删除所选工程" in dialog.message_text()
        dialog.confirm_delete()
        wait_for_project_deleted(main_page, target_project)
        print(f"已确认删除：{target_project}")

    assert project_list.project_names() == ["工程1", "工程2"]
    main_page.focus()
    keyboard.send_keys("^s")
    time.sleep(0.3)
    solution_sdk.save_solution()
    sdk_projects = [proj.name for proj in solution_sdk.get_projects()]
    print(f"删除后 SDK 工程列表：{sdk_projects}")
    assert set(sdk_projects) == {"工程1", "工程2"}
