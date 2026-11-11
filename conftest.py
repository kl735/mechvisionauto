# coding: utf-8
"""Mech-Vision UI 测试的 pytest 公共夹具。"""

import time
import pytest
from pages.main_window_page import MainWindowPage
from pages.welcome_page import WelcomePage
from pywinauto import Application
from utils.mech_vision_app import EXE_PATH, MechVisionApp
from pywinauto.application import ProcessNotFoundError

def wait_for_main_window(timeout: float = 60) -> int:
    """用 Win32 Application 等待主窗口并返回句柄。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            app = Application(backend="win32").connect(
                path=str(EXE_PATH),
                timeout=2,
            )
            window = app.window(
                title="Mech-Vision",
                class_name="Qt5152QWindowIcon",
                top_level_only=True,
            )
            if window.exists(timeout=2) and window.is_visible():
                return window.handle
        except ProcessNotFoundError:
            pass
        time.sleep(0.2)
    raise TimeoutError(f"{timeout} 秒内未找到 Mech-Vision 主窗口")


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
            try:
                welcome = WelcomePage.attach(mech_app.app, timeout=3)
                welcome.create_empty_solution_button().invoke()
            except Exception:
                pass
            main_handle = wait_for_main_window(timeout=60)

    mech_app.app = Application(backend="win32").connect(handle=main_handle)
    return MainWindowPage.attach(main_handle, timeout=60)


@pytest.fixture
def welcome_page(mech_app) -> WelcomePage:
    """提供已进入欢迎页的 Mech-Vision 欢迎页 Page。"""
    if mech_app.app is None:
        raise RuntimeError("Mech-Vision 尚未启动")
    page = WelcomePage.attach(mech_app.app, timeout=30)
    return page