# coding: utf-8
"""欢迎页测试专用夹具。"""

import pytest

from pages.main_window_page import MainWindowPage
from pages.welcome_page import WelcomePage
from utils.mech_vision_app import MechVisionApp, wait_for_main_window


@pytest.fixture
def mech_app():
    """为每条欢迎页用例独立启动并清理 Mech-Vision。"""
    app = MechVisionApp()
    try:
        yield app.start()
    finally:
        app.close()


@pytest.fixture
def main_page(mech_app) -> MainWindowPage:
    """提供本次用例的主窗口；程序已在主窗口时直接连接。"""
    if mech_app.app is None:
        raise RuntimeError("Mech-Vision 尚未启动")

    try:
        main_handle = wait_for_main_window(timeout=3)
    except TimeoutError:
        welcome = WelcomePage.attach(mech_app.app)
        welcome.create_empty_solution()
        main_handle = wait_for_main_window(timeout=60)

    return MainWindowPage.attach(main_handle, timeout=60)
