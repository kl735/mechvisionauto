# coding: utf-8
"""验证从工具箱菜单打开并定位“误差分析”窗口。"""

from pages.accuracy_error_analysis_page import AccuracyErrorAnalysisPage
from pages.main_window_page import MainWindowPage


def test_open_accuracy_error_analysis(
    main_page: MainWindowPage,
) -> None:
    """点击精度误差分析工具并验证新窗口及关键控件。"""
    try:
        opened_page = AccuracyErrorAnalysisPage.wait_for_open(
            main_page.handle,
            timeout=0.5,
        )
        opened_page.close()
    except TimeoutError:
        pass

    analysis_page = main_page.title_bar.open_accuracy_error_analysis()
    try:
        info = analysis_page.element_info
        assert info.name == AccuracyErrorAnalysisPage.TITLE
        assert info.class_name == AccuracyErrorAnalysisPage.CLASS_NAME
        assert (
            info.automation_id
            == AccuracyErrorAnalysisPage.AUTOMATION_ID
        )
        assert analysis_page.exists()

        for navigation in (
            "工具介绍",
            "相机",
            "机器人",
            "外参",
            "视觉系统漂移自校正",
        ):
            assert analysis_page.navigation_item(
                navigation
            ).is_visible()

        assert analysis_page.close_button().is_visible()
    finally:
        if analysis_page.is_visible():
            analysis_page.close()
