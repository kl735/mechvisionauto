# coding: utf-8
"""AI 分类配置向导测试夹具。"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import time

import pytest
import win32con  # pyright: ignore[reportMissingModuleSource]
import win32gui  # pyright: ignore[reportMissingModuleSource]

from pages.ai_classification_config_page import AiClassificationConfigPage
from pages.main_window_page import MainWindowPage
from services import VisionSdkClient
from utils.image_locator import TEMPLATE_DIR, click_match, locate_template


DEFAULT_SOLUTION_PATH = Path(
    r"D:\project\Mech-Vision & Mech-Viz-2.2.2-dev-10-27"
    r"\Mech-Vision\basic_config_wizard"
)
SOLUTION_PATH = Path(
    os.getenv("MECHVISION_AI_SOLUTION_PATH", str(DEFAULT_SOLUTION_PATH))
)
PROJECT_NAME = "工程1"
STEP_NAME = "AI分类（正反/有无）_1"
STEP_TITLE_TEMPLATE = TEMPLATE_DIR / "ai_classify_title.png"


def _open_solution(solution_path: Path) -> None:
    """通过 SDK 打开方案并确认目标工程和 Step 存在。"""
    if not solution_path.is_dir():
        raise FileNotFoundError(
            "未找到 AI 分类测试方案："
            f"{solution_path}\n"
            "可通过环境变量 MECHVISION_AI_SOLUTION_PATH 指定其他方案。"
        )

    with VisionSdkClient() as sdk:
        sdk.open_solution(solution_path)
        project_names = [project.name for project in sdk.get_projects()]
        if PROJECT_NAME not in project_names:
            raise RuntimeError(
                f"方案中未找到工程 {PROJECT_NAME!r}：{project_names}"
            )
        step_names = sdk.get_step_names(PROJECT_NAME)
        if STEP_NAME not in step_names:
            raise RuntimeError(
                f"{PROJECT_NAME!r} 中未找到 Step {STEP_NAME!r}："
                f"{step_names}"
            )


def _open_config_wizard(main_page: MainWindowPage) -> None:
    """图像匹配选中目标 Step，并通过 UIA 从步骤参数区域打开配置向导。"""
    win32gui.ShowWindow(main_page.handle, win32con.SW_MAXIMIZE)
    time.sleep(0.5)
    main_page.focus()
    main_page.project_list.select(PROJECT_NAME)

    match, _screenshot, _origin = locate_template(
        STEP_TITLE_TEMPLATE,
        threshold=0.8,
        timeout=15,
        hwnd=main_page.handle,
        scales=(0.75, 0.9, 1.0, 1.1, 1.25, 1.5),
    )
    click_match(match, offset=(0.25, 0.5))
    time.sleep(0.5)

    main_page.open_config_wizard()


@pytest.fixture(scope="session")
def ai_classification_page(
    main_page: MainWindowPage,
    tmp_path_factory: pytest.TempPathFactory,
) -> AiClassificationConfigPage:
    """打开固定方案并提供 AI 分类配置向导页面对象。"""
    try:
        page = AiClassificationConfigPage.wait_for_open(
            main_page.handle,
            timeout=2,
        )
    except TimeoutError:
        if not SOLUTION_PATH.is_dir():
            raise FileNotFoundError(
                "未找到 AI 分类测试方案："
                f"{SOLUTION_PATH}\n"
                "可通过环境变量 MECHVISION_AI_SOLUTION_PATH 指定其他方案。"
            )
        solution_copy = (
            tmp_path_factory.mktemp("ai_classification_solution")
            / "solution"
        )
        shutil.copytree(SOLUTION_PATH, solution_copy)

        _open_solution(solution_copy)
        time.sleep(1)
        _open_config_wizard(main_page)
        page = AiClassificationConfigPage.wait_for_open(
            main_page.handle,
            timeout=30,
        )
    win32gui.ShowWindow(page.handle, win32con.SW_RESTORE)
    win32gui.SetWindowPos(
        page.handle,
        win32con.HWND_TOP,
        20,
        20,
        1600,
        1000,
        win32con.SWP_SHOWWINDOW,
    )
    win32gui.ShowWindow(page.handle, win32con.SW_MAXIMIZE)
    time.sleep(1)
    yield page
