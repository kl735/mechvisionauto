# coding: utf-8
"""打开固定的删除测试方案，截图定位 Step 后删除，并用 SDK 断言。"""

import time
from pathlib import Path

import pytest
import win32con  # pyright: ignore[reportMissingModuleSource]
import win32gui  # pyright: ignore[reportMissingModuleSource]
from pywinauto import mouse

from pages.context_menu_page import ContextMenuPage
from pages.main_window_page import MainWindowPage
from services import VisionSdkClient
from tests.test_create_step import STEP_NAME
from utils.image_locator import (
    TEMPLATE_DIR,
    capture_window,
    click_match,
    find_mech_vision_hwnd,
    locate_template,
    press_delete,
)


SOLUTION_PATH = Path(
   "D:/project/Mech-Vision & Mech-Viz-2.2.2-dev-10-27/Mech-Vision/delete_the_test_plan"
)
TEMPLATE_PATH = TEMPLATE_DIR / "ai_classify_title.png"
DELETE_MENU_PREVIEW = (
    Path(__file__).resolve().parent.parent
    / "artifacts"
    / "delete_menu_target.png"
)
AFTER_DELETE_PREVIEW = (
    Path(__file__).resolve().parent.parent
    / "artifacts"
    / "after_delete.png"
)
SDK_WAIT = 10
CONTEXT_MENU_PROJECT = "工程1"
DELETE_KEY_PROJECT = "工程2"
TARGET_STEP_NAME = f"{STEP_NAME}_1"


def maximize_mech_vision() -> None:
    """最大化 Mech-Vision，避免窗口尺寸变化导致模板匹配失败。"""
    hwnd = find_mech_vision_hwnd()
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
    time.sleep(0.8)


def step_exists(sdk: VisionSdkClient, project_name: str, step_name: str) -> bool:
    """通过 SDK 判断指定工程中是否还存在该 Step。"""
    return step_name in sdk.get_step_names(project_name)


def wait_until_step_deleted(
    sdk: VisionSdkClient,
    project_name: str,
    step_name: str,
) -> bool:
    """等待 SDK 确认指定工程中的目标 Step 已删除。"""
    deadline = time.monotonic() + SDK_WAIT
    while time.monotonic() < deadline:
        if not step_exists(sdk, project_name, step_name):
            return True
        time.sleep(0.3)
    return False


def delete_by_context_menu(match) -> None:
    """右键 Step 并点击菜单中的“删除”。"""
    main_hwnd = find_mech_vision_hwnd()
    point = (
        match.left + int(match.width * 0.25),
        match.top + int(match.height * 0.5),
    )
    mouse.click(button="right", coords=point)
    context_menu = ContextMenuPage.wait_for_open(main_hwnd)
    preview = context_menu.save_item_preview("删除", DELETE_MENU_PREVIEW)
    print(f"删除菜单项定位截图：{preview}")
    context_menu.delete()
    print("已通过右键菜单删除")
    time.sleep(2)
    screenshot, _origin = capture_window(main_hwnd)
    AFTER_DELETE_PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    screenshot.save(AFTER_DELETE_PREVIEW)
    print(f"删除后的工程截图：{AFTER_DELETE_PREVIEW}")


def delete_by_keyboard(match) -> None:
    """选中 Step 后按 Delete 删除。"""
    click_match(match, offset=(0.25, 0.5))
    time.sleep(0.3)
    press_delete()
    print("已通过 Delete 键删除")


@pytest.mark.parametrize(
    ("delete_step", "method_name", "project_name"),
    [
        (delete_by_context_menu, "右键菜单", CONTEXT_MENU_PROJECT),
        (delete_by_keyboard, "Delete 键", DELETE_KEY_PROJECT),
    ],
    ids=["context_menu", "delete_key"],
)
def test_delete_created_step(
    main_page: MainWindowPage,
    delete_step,
    method_name: str,
    project_name: str,
) -> None:
    """打开删除测试方案，在指定工程中定位并删除 Step，再用 SDK 确认。"""
    if not SOLUTION_PATH.is_dir():
        raise FileNotFoundError(f"未找到删除测试方案：{SOLUTION_PATH}")

    print(f"打开方案：{SOLUTION_PATH}")
    print(f"删除方式：{method_name}，工程：{project_name}")

    with VisionSdkClient() as sdk:
        sdk.open_solution(SOLUTION_PATH)
        time.sleep(1.0)
        maximize_mech_vision()
        main_page.project_list.select(project_name)
        print(f"已选择工程：{project_name}")

        assert step_exists(sdk, project_name, TARGET_STEP_NAME), (
            f"删除前，SDK 未在{project_name}中找到 {TARGET_STEP_NAME!r}"
        )

        match, _screenshot, _origin = locate_template(
            TEMPLATE_PATH,
            threshold=0.8,
            timeout=15,
        )
        print(f"截图定位成功，相似度 {match.score:.3f}，中心 {match.center}")

        delete_step(match)
        step_deleted = wait_until_step_deleted(
            sdk,
            project_name,
            TARGET_STEP_NAME,
        )
        print(
            f"删除后 Step {TARGET_STEP_NAME!r} 是否已不存在："
            f"{step_deleted}"
        )
        assert step_deleted, (
            f"{project_name} 使用{method_name}删除后，"
            f"SDK 仍能查到 {TARGET_STEP_NAME!r}"
        )
