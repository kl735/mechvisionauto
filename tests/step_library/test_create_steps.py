# coding: utf-8
"""步骤库创建 Step 测试：
1. 创建单个 Step 并通过 SDK 校验；
2. 连续创建多个 Step 并通过 SDK 校验。
"""

import re
import time
from pathlib import Path

from pywinauto import keyboard

from pages.main_window_page import MainWindowPage
from services import VisionSdkClient
from utils.image_locator import press_delete


STEP_NAME = "AI分类（正反/有无）"
STEP_COUNT = 3
COLUMNS = 3


def clear_canvas_steps(main_page: MainWindowPage) -> None:
    """清空当前工程画布中的所有 Step。"""
    main_page.focus()
    main_page.project_editor.canvas().click_input()
    time.sleep(0.2)
    keyboard.send_keys("^a")
    time.sleep(0.2)
    press_delete()
    time.sleep(0.3)


def canvas_destinations(
    canvas_rect,
    count: int = STEP_COUNT,
    columns: int = COLUMNS,
) -> list[tuple[int, int]]:
    """按网格错开落点，避免多个步骤叠在同一位置。"""
    points: list[tuple[int, int]] = []
    for index in range(count):
        column = index % columns
        row = index // columns
        x_ratio = 0.28 + column * 0.22
        y_ratio = 0.28 + row * 0.22
        points.append(
            (
                round(canvas_rect.left + canvas_rect.width() * x_ratio),
                round(canvas_rect.top + canvas_rect.height() * y_ratio),
            )
        )
    return points


def test_01_create_single_step(
    main_page: MainWindowPage,
    tmp_path: Path,
) -> None:
    """用例1：创建 1 个 Step 并通过 SDK 校验。"""
    clear_canvas_steps(main_page)
    step_library = main_page.step_library
    step_library.dock()
    step_item = step_library.locate(STEP_NAME)

    main_page.focus()
    destination = main_page.project_editor.canvas_point(0.40, 0.35)
    step_library.drag_item_to(step_item, destination)
    print(f"已拖放：{STEP_NAME} 到画布 {destination}")

    solution_path = tmp_path / "step_name_assert_solution"
    with VisionSdkClient() as sdk:
        sdk.save_solution(solution_path)
        print(f"已保存方案：{solution_path}")

        projects = sdk.get_projects()
        assert projects, "保存后的方案中没有工程"

        step_names = sdk.get_step_names()
        print(f"SDK 获取到的 Step：{step_names}")
        step_name_pattern = re.compile(rf"^{re.escape(STEP_NAME)}(?:_\d+)?$")
        assert any(step_name_pattern.fullmatch(name) for name in step_names), (
            f"SDK 未找到拖入的 Step：期望 {STEP_NAME!r} "
            f"或 {STEP_NAME}_N，实际 {step_names!r}"
        )


def test_02_create_multiple_steps(
    main_page: MainWindowPage,
    tmp_path: Path,
) -> None:
    """用例2：重复拖入多个 Step 并通过 SDK 校验。"""
    clear_canvas_steps(main_page)
    step_library = main_page.step_library
    step_library.dock()

    canvas = main_page.project_editor.canvas()
    destinations = canvas_destinations(canvas.rectangle(), STEP_COUNT)

    for index, destination in enumerate(destinations, start=1):
        main_page.focus()
        step_item = step_library.locate(STEP_NAME)
        step_library.drag_item_to(step_item, destination)
        print(f"已拖放第 {index} 个：{STEP_NAME} 到画布 {destination}")

    solution_path = tmp_path / "multiple_steps_assert_solution"
    with VisionSdkClient() as sdk:
        sdk.save_solution(solution_path)
        print(f"已保存方案：{solution_path}")

        projects = sdk.get_projects()
        assert projects, "保存后的方案中没有工程"

        step_names = sdk.get_step_names()
        print(f"SDK 获取到的 Step：{step_names}")
        expected_names = [
            f"{STEP_NAME}_{index}" for index in range(1, STEP_COUNT + 1)
        ]
        missing_names = [
            name for name in expected_names if name not in step_names
        ]
        assert not missing_names, (
            f"SDK 未找到全部拖入的 Step：缺少 {missing_names!r}，实际 {step_names!r}"
        )
    clear_canvas_steps(main_page)
