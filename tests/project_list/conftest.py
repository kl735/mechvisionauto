# coding: utf-8
"""工程列表（project_list）模块测试的公共配置、夹具与业务辅助函数。"""

from __future__ import annotations

import time
from collections.abc import Iterator
from pathlib import Path

import pytest
import win32con  # pyright: ignore[reportMissingModuleSource]
import win32gui  # pyright: ignore[reportMissingModuleSource]
from pywinauto import keyboard, mouse

from pages.main_window_page import MainWindowPage
from services import VisionSdkClient
from utils.image_locator import (
    TEMPLATE_DIR,
    find_mech_vision_hwnd,
    locate_template,
    press_delete,
)
from utils.window_helper import set_per_monitor_dpi_awareness


SOLUTION_PATH = Path(
    "C:/Users/mech-mind/AppData/Local/Temp/pytest-of-mech-mind/"
    "pytest-56/test_create_and_delete_project0/delete_step_solution"
)
SOLUTION_NAME = "delete_step_solution"
STEP_TEMPLATE = TEMPLATE_DIR / "ai_classify_title.png"
PROJECT_COPY_PAIRS = (
    ("工程1", "工程3"),
    ("工程2", "工程4"),
)


def wait_for_solution_loaded(
    main_page: MainWindowPage,
    solution_name: str = SOLUTION_NAME,
) -> None:
    """等待工程树加载出目标方案节点。"""
    project_list = main_page.project_list
    deadline = time.monotonic() + project_list.timeout
    while time.monotonic() < deadline:
        if project_list.item(solution_name).exists(timeout=0.2):
            return
        time.sleep(0.2)
    raise TimeoutError(f"工程树未显示方案：{solution_name}")


def wait_for_project_created(
    main_page: MainWindowPage,
    project_name: str,
    timeout: float = 10,
) -> None:
    """等待新建工程节点出现在工程树中。"""
    project_list = main_page.project_list
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if project_name in project_list.project_names():
            return
        time.sleep(0.2)
    raise TimeoutError(f"新建工程后工程树中未出现：{project_name}")


def wait_for_project_deleted(
    main_page: MainWindowPage,
    project_name: str,
    timeout: float = 10,
) -> None:
    """等待指定工程从工程树中消失。"""
    project_list = main_page.project_list
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if project_name not in project_list.project_names():
            return
        time.sleep(0.2)
    raise TimeoutError(f"删除工程后节点仍然存在：{project_name}")


def wait_for_project_steps_empty(
    sdk: VisionSdkClient,
    project_name: str,
    timeout: float = 10,
) -> None:
    """等待指定工程中的所有 Step 被删空。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not sdk.get_step_names(project_name):
            return
        time.sleep(0.2)
    raise TimeoutError(
        f"{project_name} 删除 Step 后仍存在：{sdk.get_step_names(project_name)}"
    )


def copy_all_steps_to_new_project(
    sdk: VisionSdkClient,
    main_page: MainWindowPage,
    source_project: str,
    target_project: str,
    solution_name: str = SOLUTION_NAME,
) -> list[str]:
    """选中源工程，通过 Ctrl+A/Ctrl+C 全选复制 Step，新建目标工程并粘贴校验。"""
    project_list = main_page.project_list
    project_list.select(source_project)
    source_steps = sdk.get_step_names(source_project)
    print(f"{source_project} 原始 Step：{source_steps}")
    assert source_steps, f"{source_project} 中没有可复制的 Step"

    main_page.project_editor.canvas().click_input()
    time.sleep(0.2)
    keyboard.send_keys("^a")
    time.sleep(0.2)
    keyboard.send_keys("^c")
    time.sleep(0.2)

    project_list.open_solution_menu(solution_name).click_item("新建工程")
    wait_for_project_created(main_page, target_project)

    project_list.select(target_project)
    main_page.project_editor.canvas().click_input()
    time.sleep(0.2)
    keyboard.send_keys("^v")
    time.sleep(0.2)
    keyboard.send_keys("^s")
    time.sleep(0.5)

    deadline = time.monotonic() + 10
    copied_steps: list[str] = []
    while time.monotonic() < deadline:
        copied_steps = sdk.get_step_names(target_project)
        if copied_steps:
            break
        time.sleep(0.3)

    print(f"{target_project} 粘贴后的 Step：{copied_steps}")
    assert copied_steps, f"{target_project} 中未粘贴出任何 Step"
    assert len(copied_steps) == len(source_steps), (
        f"{source_project} Step 数量为 {len(source_steps)}，"
        f"{target_project} Step 数量为 {len(copied_steps)}"
    )
    assert sorted(copied_steps) == sorted(source_steps), (
        f"{source_project} 与 {target_project} 的 Step 不一致："
        f"{source_steps} vs {copied_steps}"
    )
    assert sdk.get_step_names(source_project) == source_steps
    return copied_steps


def delete_project_step_by_context_menu(
    sdk: VisionSdkClient,
    main_page: MainWindowPage,
    project_name: str,
) -> None:
    """方式1：选中工程，图像定位 Step 后通过右键菜单点击“删除”，并用 SDK 校验。"""
    main_page.project_list.select(project_name)
    before_steps = sdk.get_step_names(project_name)
    assert before_steps, f"{project_name} 删除前没有 Step"

    hwnd = find_mech_vision_hwnd()
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
    time.sleep(0.5)

    match, _screenshot, _origin = locate_template(
        STEP_TEMPLATE,
        threshold=0.8,
        timeout=15,
    )
    set_per_monitor_dpi_awareness()
    point = (
        match.left + int(match.width * 0.25),
        match.top + int(match.height * 0.5),
    )
    mouse.click(button="right", coords=point)
    context_menu = main_page.project_editor.wait_for_step_context_menu()
    context_menu.delete()

    wait_for_project_steps_empty(sdk, project_name)
    keyboard.send_keys("^s")
    time.sleep(0.3)
    print(f"已通过右键菜单删除 {project_name} 中的 Step：{before_steps}")


def delete_project_steps_by_delete_key(
    sdk: VisionSdkClient,
    main_page: MainWindowPage,
    project_name: str,
) -> None:
    """方式2：选中工程，在画布中选中 Step 后按 Delete 键删除，并用 SDK 校验。"""
    main_page.project_list.select(project_name)
    before_steps = sdk.get_step_names(project_name)
    assert before_steps, f"{project_name} 删除前没有 Step"

    main_page.project_editor.canvas().click_input()
    time.sleep(0.2)
    keyboard.send_keys("^a")
    time.sleep(0.2)
    press_delete()

    wait_for_project_steps_empty(sdk, project_name)
    keyboard.send_keys("^s")
    time.sleep(0.3)
    print(f"已通过 Delete 键删除 {project_name} 中的 Step：{before_steps}")


@pytest.fixture(scope="module")
def solution_sdk(
    main_page: MainWindowPage,
) -> Iterator[VisionSdkClient]:
    """模块级夹具：直接打开 SOLUTION_PATH 供同模块内先后测试共享方案会话。"""
    assert SOLUTION_PATH.is_dir(), f"测试方案不存在：{SOLUTION_PATH}"
    with VisionSdkClient() as sdk:
        sdk.open_solution(SOLUTION_PATH)
        wait_for_solution_loaded(main_page)
        yield sdk
