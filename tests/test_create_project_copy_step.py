# coding: utf-8
"""新建工程，将工程1的 Step 复制到新工程并保存。"""

import json
import shutil
import time
from pathlib import Path

import win32con  # pyright: ignore[reportMissingModuleSource]
import win32gui  # pyright: ignore[reportMissingModuleSource]
from pywinauto import keyboard

from pages.main_window_page import MainWindowPage
from services import VisionSdkClient
from tests.test_create_step import STEP_NAME
from utils.image_locator import (
    TEMPLATE_DIR,
    click_match,
    find_mech_vision_hwnd,
    locate_template,
)
from utils.window_helper import set_per_monitor_dpi_awareness


SOURCE_SOLUTION_PATH = Path(
    "D:/project/Mech-Vision & Mech-Viz-2.2.2-dev-10-27/"
    "Mech-Vision/delete_the_test_plan"
)
SOLUTION_NAME = "delete_step_solution"
STEP_TEMPLATE = TEMPLATE_DIR / "ai_classify_title.png"
WAIT_TIMEOUT = 10
PROJECT_COPY_PAIRS = (
    ("工程1", "工程3"),
    ("工程2", "工程4"),
)


def prepare_solution_copy(destination: Path) -> None:
    """复制并标准化测试方案，使其初始状态仅包含工程1和工程2。"""
    shutil.copytree(SOURCE_SOLUTION_PATH, destination)

    retained_projects = {"工程1", "工程2"}
    for child in destination.iterdir():
        if (
            child.is_dir()
            and child.name.startswith("工程")
            and child.name not in retained_projects
        ):
            shutil.rmtree(child)

    solution_file = destination / ".msoln"
    solution_data = json.loads(solution_file.read_text(encoding="utf-8"))
    solution_data["vis_projects"] = {
        "工程1": 1,
        "工程2": 2,
    }
    solution_file.write_text(
        json.dumps(solution_data, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )


def wait_for_project_steps(
    sdk: VisionSdkClient,
    project_name: str,
    timeout: float = WAIT_TIMEOUT,
) -> list[str]:
    """等待指定工程中出现 Step，并返回 Step 名称。"""
    deadline = time.monotonic() + timeout
    step_names: list[str] = []
    while time.monotonic() < deadline:
        step_names = sdk.get_step_names(project_name)
        if step_names:
            return step_names
        time.sleep(0.3)
    return step_names


def copy_step_to_new_project(
    sdk: VisionSdkClient,
    main_page: MainWindowPage,
    source_project: str,
    expected_project: str,
) -> list[str]:
    """复制源工程的 Step，新建工程并粘贴，返回新工程 Step。"""
    main_page.project_list.select(source_project)
    source_steps = sdk.get_step_names(source_project)
    assert source_steps, f"{source_project} 中没有可复制的 Step"

    match, _screenshot, _origin = locate_template(
        STEP_TEMPLATE,
        threshold=0.8,
        timeout=15,
    )
    set_per_monitor_dpi_awareness()
    click_match(match, offset=(0.25, 0.5))
    keyboard.send_keys("^c")
    print(f"已从 {source_project} 复制 Step：{source_steps}")

    new_project = main_page.project_list.create_project(SOLUTION_NAME)
    assert new_project == expected_project, (
        f"期望新建 {expected_project!r}，实际为 {new_project!r}"
    )
    main_page.project_list.select(new_project)
    main_page.focus()
    keyboard.send_keys("^v")

    copied_steps = wait_for_project_steps(sdk, new_project)
    assert copied_steps, f"{new_project} 中未出现复制的 Step"
    assert any(
        name.startswith(STEP_NAME)
        for name in copied_steps
    ), f"{new_project} 中未找到目标 Step：{copied_steps}"
    print(f"已将 {source_project} 的 Step 复制到 {new_project}")
    return copied_steps


def test_create_project_copy_step_and_save(
    main_page: MainWindowPage,
    tmp_path: Path,
) -> None:
    """在方案副本中新建工程，复制工程1的 Step，保存后用 SDK 验证。"""
    if not SOURCE_SOLUTION_PATH.is_dir():
        raise FileNotFoundError(
            f"未找到源测试方案：{SOURCE_SOLUTION_PATH}"
        )

    solution_copy = tmp_path / SOLUTION_NAME
    prepare_solution_copy(solution_copy)

    with VisionSdkClient() as sdk:
        sdk.open_solution(solution_copy)
        time.sleep(1)

        hwnd = find_mech_vision_hwnd()
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        time.sleep(0.8)

        copied_projects: dict[str, list[str]] = {}
        for source_project, target_project in PROJECT_COPY_PAIRS:
            copied_projects[target_project] = copy_step_to_new_project(
                sdk,
                main_page,
                source_project,
                target_project,
            )

        main_page.focus()
        keyboard.send_keys("^s")
        time.sleep(0.5)
        sdk.save_solution()
        print(f"已保存方案：{copied_projects}")

    with VisionSdkClient() as verifier:
        verifier.open_solution(solution_copy)
        for _source_project, target_project in PROJECT_COPY_PAIRS:
            saved_steps = verifier.get_step_names(target_project)
            assert any(
                name.startswith(STEP_NAME)
                for name in saved_steps
            ), (
                f"重新打开方案后，{target_project} 中未找到复制的 Step："
                f"{saved_steps}"
            )
            print(
                f"SDK 持久化验证成功：{target_project} -> "
                f"{saved_steps}"
            )
