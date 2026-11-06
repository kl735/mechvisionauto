# coding: utf-8
"""测试步骤库 Page：新建空白方案后，搜索步骤并拖到画布。"""

import re
from pathlib import Path

from pages.main_window_page import MainWindowPage
from services import VisionSdkClient


STEP_NAME = "AI分类（正反/有无）"


def test_search_and_drag_2d_smart_camera(
    main_page: MainWindowPage,
    tmp_path: Path,
) -> None:
    """拖入 Step、保存方案，并通过 SDK 校验 Step 名称。"""
    step_library = main_page.step_library
    step_library.dock()
    print("步骤库定位成功")

    camera_step = step_library.locate(STEP_NAME)
    step_rect = camera_step.rectangle()
    print(
        f"已找到步骤：{camera_step.window_text()} "
        f"(L{step_rect.left}, T{step_rect.top}, "
        f"R{step_rect.right}, B{step_rect.bottom})"
    )

    canvas = main_page.project_editor.canvas()
    print("画布定位成功")

    main_page.focus()
    canvas_rect = canvas.rectangle()
    destination = (
        round(canvas_rect.left + canvas_rect.width() * 0.40),
        round(canvas_rect.top + canvas_rect.height() * 0.35),
    )
    step_library.drag_item_to(camera_step, destination)
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
