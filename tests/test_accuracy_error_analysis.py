# coding: utf-8
"""验证“误差分析”窗口打开、左侧导航切换及四个右侧子页面控件定位。"""

from pages.accuracy_error_analysis_page import AccuracyErrorAnalysisPage
from pages.main_window_page import MainWindowPage


def test_open_accuracy_error_analysis(
    main_page: MainWindowPage,
) -> None:
    """依次点击工具介绍、相机、机器人、外参，并验证各右侧子页面的控件定位。"""
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

        # 1. 工具介绍页面
        intro_panel = analysis_page.click_tool_introduction()
        assert intro_panel.is_open()
        assert intro_panel.intro_banner_text()
        assert intro_panel.prompt_label().is_visible()
        for choice in ("是", "否"):
            assert intro_panel.eih_same_position_option(
                choice
            ).is_visible()
            assert intro_panel.point_cloud_quality_option(
                choice
            ).is_visible()
        for choice in (
            "位置相近",
            "有明显的XYZ方向平移",
            "有明显的旋转",
        ):
            assert intro_panel.workpiece_position_option(
                choice
            ).is_visible()
        assert intro_panel.evaluate_button().is_visible()
        assert intro_panel.suggested_check_label().is_visible()

        # 2. 相机页面
        camera_panel = analysis_page.click_camera()
        assert camera_panel.is_open()
        assert camera_panel.card_titles() == ["检查相机内参"]
        assert camera_panel.intrinsic_check_button().is_visible()

        # 3. 机器人页面
        robot_panel = analysis_page.click_robot()
        assert robot_panel.is_open()
        assert robot_panel.card_titles() == [
            "DH参数检查",
            "机器人绝对精度检查",
            "机器人重复精度检查",
        ]
        assert robot_panel.dh_parameter_check_button().is_visible()
        assert robot_panel.absolute_accuracy_check_button().is_visible()
        assert robot_panel.repeatability_check_button().is_visible()

        dh_panel = robot_panel.click_dh_parameter_check()
        assert dh_panel.is_open()
        assert dh_panel.explanation()
        robot_panel = dh_panel.click_previous()

        absolute_panel = robot_panel.click_absolute_accuracy_check()
        assert absolute_panel.is_open()
        assert absolute_panel.instruction()
        move_panel = absolute_panel.click_next()
        assert move_panel.instruction()
        rotation_panel = move_panel.click_next()
        assert rotation_panel.operation_steps()
        recommendations_panel = rotation_panel.click_next()
        assert len(recommendations_panel.recommendation_texts()) == 2
        rotation_panel = recommendations_panel.click_previous()
        move_panel = rotation_panel.click_previous()
        absolute_panel = move_panel.click_previous()
        robot_panel = absolute_panel.click_previous()

        repeatability_panel = robot_panel.click_repeatability_check()
        assert repeatability_panel.is_open()
        assert len(repeatability_panel.step_descriptions()) == 4
        assert repeatability_panel.eih_photo_position_label().is_visible()
        assert repeatability_panel.fixed_grasp_point_label().is_visible()
        operation_panel = repeatability_panel.click_next()
        assert operation_panel.operation_steps()
        evaluation_panel = operation_panel.click_next()
        assert evaluation_panel.table_header_names() == [
            "拍照次序",
            "标定板位姿数据",
        ]
        assert evaluation_panel.pose_table().is_visible()
        assert evaluation_panel.evaluate_error_button().is_visible()
        operation_panel = evaluation_panel.click_previous()
        repeatability_panel = operation_panel.click_previous()
        repeatability_panel.click_previous()

        # 4. 外参页面
        extrinsic_panel = analysis_page.click_extrinsic_parameters()
        assert extrinsic_panel.is_open()
        assert extrinsic_panel.card_titles() == [
            "EIH外参误差分析",
            "ETH外参误差分析",
        ]
        assert extrinsic_panel.eih_extrinsic_analysis_button().is_visible()
        assert extrinsic_panel.eth_extrinsic_analysis_button().is_visible()

        eih_project = extrinsic_panel.click_eih_extrinsic_analysis()
        assert len(eih_project.step_descriptions()) == 5
        eih_operation = eih_project.click_next()
        assert eih_operation.instruction()
        eih_evaluation = eih_operation.click_next()
        assert eih_evaluation.table_header_names() == [
            "拍照次序",
            "标定板位姿数据",
        ]
        assert eih_evaluation.pose_table().is_visible()
        assert eih_evaluation.evaluate_error_button().is_visible()
        eih_operation = eih_evaluation.click_previous()
        eih_project = eih_operation.click_previous()
        extrinsic_panel = eih_project.click_previous()

        eth_project = extrinsic_panel.click_eth_extrinsic_analysis()
        assert len(eth_project.step_descriptions()) == 4
        point_cloud = eth_project.click_next()
        assert point_cloud.operation_steps()
        virtual_tcp = point_cloud.click_next()
        assert virtual_tcp.operation_steps()
        other_area = virtual_tcp.click_next()
        assert other_area.operation_steps()
        eth_recommendations = other_area.click_next()
        assert len(eth_recommendations.recommendation_texts()) == 2
        other_area = eth_recommendations.click_previous()
        virtual_tcp = other_area.click_previous()
        point_cloud = virtual_tcp.click_previous()
        eth_project = point_cloud.click_previous()
        eth_project.click_previous()
    finally:
        if analysis_page.is_visible():
            analysis_page.close()


def test_print_accuracy_error_analysis_contents(
    main_page: MainWindowPage,
) -> None:
    """遍历误差分析各级页面并打印已封装的文本，不执行断言。"""
    try:
        opened_page = AccuracyErrorAnalysisPage.wait_for_open(
            main_page.handle,
            timeout=0.5,
        )
        opened_page.close()
    except TimeoutError:
        pass

    def print_section(title: str, content) -> None:
        print(f"\n{'=' * 20} {title} {'=' * 20}")
        if isinstance(content, dict):
            for name, value in content.items():
                print(f"{name}: {value}")
            return
        if isinstance(content, (list, tuple)):
            for value in content:
                print(value)
            return
        print(content)

    analysis_page = main_page.title_bar.open_accuracy_error_analysis()
    try:
        # 相机内参检查
        camera = analysis_page.click_camera()
        camera_detail = camera.click_intrinsic_check()
        print_section("相机内参页面全部文本", camera_detail.text_contents())
        print_section(
            "相机内参步骤说明",
            camera_detail.step_descriptions(),
        )
        camera_detail.click_previous()

        # 机器人：DH 参数检查
        robot = analysis_page.click_robot()
        dh_panel = robot.click_dh_parameter_check()
        print_section("DH参数检查", dh_panel.explanation())
        robot = dh_panel.click_previous()

        # 机器人：绝对精度检查完整向导
        absolute = robot.click_absolute_accuracy_check()
        print_section("机器人绝对精度-零点检查", absolute.instruction())
        move = absolute.click_next()
        print_section("机器人绝对精度-移动距离检查", move.instruction())
        rotation = move.click_next()
        print_section(
            "机器人绝对精度-围绕尖点旋转",
            rotation.operation_steps(),
        )
        absolute_recommendations = rotation.click_next()
        print_section(
            "机器人绝对精度-处理建议",
            absolute_recommendations.recommendation_texts(),
        )
        rotation = absolute_recommendations.click_previous()
        move = rotation.click_previous()
        absolute = move.click_previous()
        robot = absolute.click_previous()

        # 机器人：重复精度检查完整向导
        repeatability = robot.click_repeatability_check()
        print_section(
            "机器人重复精度-工程搭建步骤",
            repeatability.step_descriptions(),
        )
        repeatability_operation = repeatability.click_next()
        print_section(
            "机器人重复精度-拍照操作步骤",
            repeatability_operation.operation_steps(),
        )
        repeatability_evaluation = repeatability_operation.click_next()
        print_section(
            "机器人重复精度-评估页面文本",
            repeatability_evaluation.text_contents(),
        )
        print_section(
            "机器人重复精度-表头",
            repeatability_evaluation.table_header_names(),
        )
        repeatability_operation = (
            repeatability_evaluation.click_previous()
        )
        repeatability = repeatability_operation.click_previous()
        repeatability.click_previous()

        # 外参：EIH 完整向导
        extrinsic = analysis_page.click_extrinsic_parameters()
        eih_project = extrinsic.click_eih_extrinsic_analysis()
        print_section(
            "EIH外参-工程搭建步骤",
            eih_project.step_descriptions(),
        )
        eih_operation = eih_project.click_next()
        print_section("EIH外参-位姿采集", eih_operation.instruction())
        eih_evaluation = eih_operation.click_next()
        print_section(
            "EIH外参-评估页面文本",
            eih_evaluation.text_contents(),
        )
        print_section(
            "EIH外参-表头",
            eih_evaluation.table_header_names(),
        )
        eih_operation = eih_evaluation.click_previous()
        eih_project = eih_operation.click_previous()
        extrinsic = eih_project.click_previous()

        # 外参：ETH 完整向导
        eth_project = extrinsic.click_eth_extrinsic_analysis()
        print_section(
            "ETH外参-工程搭建步骤",
            eth_project.step_descriptions(),
        )
        point_cloud = eth_project.click_next()
        print_section(
            "ETH外参-获取场景点云",
            [point_cloud.operation_title(), point_cloud.operation_steps()],
        )
        virtual_tcp = point_cloud.click_next()
        print_section(
            "ETH外参-创建虚拟TCP",
            [virtual_tcp.operation_title(), virtual_tcp.operation_steps()],
        )
        other_area = virtual_tcp.click_next()
        print_section(
            "ETH外参-其他位置评估",
            [other_area.operation_title(), other_area.operation_steps()],
        )
        eth_recommendations = other_area.click_next()
        print_section(
            "ETH外参-处理建议",
            eth_recommendations.recommendation_texts(),
        )
    finally:
        if analysis_page.is_visible():
            analysis_page.close()
