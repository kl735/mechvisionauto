# coding: utf-8
"""Mech-Vision UI 测试的 pytest 公共夹具。"""

import pytest
import win32con  # pyright: ignore[reportMissingModuleSource]
import win32gui  # pyright: ignore[reportMissingModuleSource]
from pages.main_window_page import MainWindowPage
from pages.welcome_page import WelcomePage
from pywinauto import Application
from run import wait_for_main_window
from utils.mech_vision_app import MechVisionApp




@pytest.fixture(scope="session")
def mech_app():
    """测试会话开始时启动或连接，结束时关闭测试启动的程序。"""
    app = MechVisionApp()
    try:
        yield app.start()
    finally:
        app.close()


@pytest.fixture(scope="session")
def main_page(mech_app) -> MainWindowPage:
    """提供已进入空白方案的 Mech-Vision 主窗口 Page。"""
    if mech_app.app is None:
        raise RuntimeError("Mech-Vision 尚未启动")

    try:
        main_handle = wait_for_main_window(timeout=3)
    except TimeoutError:
        welcome = WelcomePage.attach(mech_app.app)
        welcome.create_empty_solution()
        try:
            main_handle = wait_for_main_window(timeout=5)
        except TimeoutError:
            welcome.create_empty_solution_button().invoke()
            main_handle = wait_for_main_window(timeout=60)

    mech_app.app = Application(backend="win32").connect(handle=main_handle)
    return MainWindowPage.attach(main_handle, timeout=60)
