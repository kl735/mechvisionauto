# coding: utf-8
"""打开固定的删除测试方案，截图定位 Step 后删除，并用 SDK 断言。"""

import time
from pathlib import Path

import pytest
import win32con  # pyright: ignore[reportMissingModuleSource]
import win32gui  # pyright: ignore[reportMissingModuleSource]
import win32process  # pyright: ignore[reportMissingModuleSource]
from pywinauto import Application, Desktop, mouse

from image_locator import (
    TEMPLATE_DIR,
    click_match,
    find_mech_vision_hwnd,
    locate_template,
    press_delete,
)
from services import VisionSdkClient
from test_create_step import STEP_NAME


SOLUTION_PATH = Path(
   "D:/project/Mech-Vision & Mech-Viz-2.2.2-dev-10-27/Mech-Vision/delete_the_test_plan"
)
TEMPLATE_PATH = TEMPLATE_DIR / "ai_classify_title.png"
SDK_WAIT = 10
CONTEXT_MENU_PROJECT = "工程1"
DELETE_KEY_PROJECT = "工程2"
TARGET_STEP_NAME = f"{STEP_NAME}_1"


def maximize_mech_vision() -> None:
    """最大化 Mech-Vision，避免窗口尺寸变化导致模板匹配失败。"""
    hwnd = find_mech_vision_hwnd()
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
    time.sleep(0.8)


def select_project(main_window, project_name: str) -> None:
    """在工程列表中选中指定工程，使画布切换到该工程。"""
    project_list = main_window.child_window(title="工程列表", control_type="Window")
    project_list.wait("exists", timeout=10)
    for title in (project_name, f"*{project_name}"):
        item = project_list.child_window(title=title, control_type="TreeItem")
        if item.exists(timeout=1):
            item.click_input()
            time.sleep(0.8)
            print(f"已选择工程：{project_name}")
            return
    raise RuntimeError(f"工程列表中未找到：{project_name}")


def step_exists(sdk: VisionSdkClient, project_name: str, step_name: str) -> bool:
    """通过 SDK 判断指定工程中是否还存在该 Step。"""
    return step_name in sdk.get_step_names(project_name)


def wait_until_deleted(
    sdk: VisionSdkClient,
    project_name: str,
    step_name: str,
) -> bool:
    """等待 SDK 确认指定工程中的目标 Step 已不存在。"""
    deadline = time.monotonic() + SDK_WAIT
    exists = step_exists(sdk, project_name, step_name)
    while time.monotonic() < deadline:
        exists = step_exists(sdk, project_name, step_name)
        if not exists:
            return False
        time.sleep(0.3)
    return exists


def _click_delete_menu_item() -> str | None:
    """在 Mech-Vision 进程的右键菜单里点击“删除”。"""
    hwnd = find_mech_vision_hwnd()
    _, process_id = win32process.GetWindowThreadProcessId(hwnd)
    popup_class_names = ("Qt5152QWindowPopup", "QMenu")
    for class_name in popup_class_names:
        popup = Desktop(backend="win32").window(
            process=process_id,
            class_name=class_name,
        )
        if not popup.exists(timeout=0.2):
            continue
        app = Application(backend="uia").connect(handle=popup.handle)
        menu_item = app.window(handle=popup.handle).child_window(
            title="删除",
            control_type="MenuItem",
        )
        if menu_item.exists(timeout=0.2):
            menu_item.click_input()
            return "删除"
    return None


def delete_by_context_menu(match) -> None:
    """右键 Step 并点击菜单中的“删除”。"""
    point = (
        match.left + int(match.width * 0.25),
        match.top + int(match.height * 0.5),
    )
    mouse.click(button="right", coords=point)

    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        clicked = _click_delete_menu_item()
        if clicked:
            print(f"已通过右键菜单删除：{clicked}")
            return
        time.sleep(0.2)
    raise TimeoutError("右键菜单中未找到“删除”")


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
    mech_win,
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
        select_project(mech_win, project_name)

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
        still_exists = wait_until_deleted(sdk, project_name, TARGET_STEP_NAME)
        print(f"删除后 {project_name} 是否仍存在：{still_exists}")
        assert not still_exists, (
            f"{project_name} 使用{method_name}删除后，"
            f"SDK 仍能查到 {TARGET_STEP_NAME!r}"
        )
