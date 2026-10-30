# coding: utf-8
"""Mech-Vision UI 测试的 pytest 公共夹具。"""

import pytest
from utils.mech_vision_app import close_mech_vision, start_mech_vision


@pytest.fixture(scope="session")
def mech_app():
    """测试会话开始时启动或连接，结束时关闭测试启动的程序。"""
    app_session = start_mech_vision()
    yield app_session
    close_mech_vision(app_session)


@pytest.fixture
def mech_win(mech_app):
    """向每个测试用例提供 Mech-Vision 主窗口。"""
    return mech_app.main_window
