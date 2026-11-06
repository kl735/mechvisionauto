# coding: utf-8
"""测试步骤库 Page：新建空白方案后，多次搜索并拖到画布。"""

from pathlib import Path

from pages.main_window_page import MainWindowPage
from services import VisionSdkClient


STEP_NAME = "AI分类（正反/有无）"
STEP_COUNT = 3
COLUMNS = 3


def canvas_destinations(canvas_rect, count: int) -> list[tuple[int, int]]:
    """按网格错开落点，避免多个步骤叠在同一位置。"""
    points = []
    for index in range(count):
        column = index % COLUMNS
        row = index // COLUMNS
        x_ratio = 0.28 + column * 0.22
        y_ratio = 0.28 + row * 0.22
        points.append(
            (
                round(canvas_rect.left + canvas_rect.width() * x_ratio),
                round(canvas_rect.top + canvas_rect.height() * y_ratio),
            )
        )
    return points


def test_create_multiple_ai_classify_steps(
    main_page: MainWindowPage,
    tmp_path: Path,
) -> None:
    """重复拖入 Step、保存方案，并通过 SDK 校验全部 Step 名称。"""
    # 定位步骤库
    step_library = main_page.step_library
    step_library.dock()
    print("步骤库定位成功")

    # 定位工程编辑区
    canvas = main_page.project_editor.canvas()
    print("画布定位成功")

    # 计算多个不重叠的落点
    destinations = canvas_destinations(canvas.rectangle(), STEP_COUNT)

    # 每次重新定位步骤库节点，再拖到对应落点
    for index, destination in enumerate(destinations, start=1):
        main_page.focus()
        step_item = step_library.locate(STEP_NAME)
        step_rect = step_item.rectangle()
        print(
            f"第 {index} 个已找到步骤：{step_item.window_text()} "
            f"(L{step_rect.left}, T{step_rect.top}, "
            f"R{step_rect.right}, B{step_rect.bottom})"
        )
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
        expected_names = [f"{STEP_NAME}_{index}" for index in range(1, STEP_COUNT + 1)]
        missing_names = [name for name in expected_names if name not in step_names]
        assert not missing_names, (
            f"SDK 未找到全部拖入的 Step：缺少 {missing_names!r}，实际 {step_names!r}"
        )
