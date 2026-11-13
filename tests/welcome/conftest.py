# coding: utf-8
"""欢迎页测试专用夹具。"""

import pytest

from utils.mech_vision_app import MechVisionApp

@pytest.fixture
def mech_app():
    """为每条欢迎页用例独立启动并清理 Mech-Vision。"""
    app = MechVisionApp()
    try:
        yield app.start()
    finally:
        app.close()
