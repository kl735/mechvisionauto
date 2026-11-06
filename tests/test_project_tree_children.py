# coding: utf-8
"""验证工程列表 QTreeView 能否获取子控件。"""

from pages.main_window_page import MainWindowPage


def test_print_project_tree_control_identifiers(
    main_page: MainWindowPage,
) -> None:
    """使用 pywinauto 完整打印工程树控件结构。"""
    main_page.project_list.print_tree_control_identifiers()


def test_print_project_tree_controls(
    main_page: MainWindowPage,
) -> None:
    """调用 Page 打印函数，并验证能获取工程树控件。"""
    controls = main_page.project_list.print_tree_controls()
    assert controls, "工程树下没有获取到任何控件"

    names = [
        control.window_text().strip()
        for control in controls
        if control.window_text().strip()
    ]
    print(f"工程树中的有效控件名称：{names}")
    assert "工程1" in names, f"工程树中未找到“工程1”：{names}"


def test_get_project_tree_children(
    main_page: MainWindowPage,
) -> None:
    """验证工程列表标题栏按钮及工程树节点均可通过 Page 定位。"""
    project_list = main_page.project_list
    title = project_list.title_label()
    assert title.window_text() == "工程列表"

    title_buttons = project_list.title_buttons()
    print(f"工程列表标题栏共定位到 {len(title_buttons)} 个按钮：")
    for index, button in enumerate(title_buttons, start=1):
        print(
            f"{index}. class_name={button.element_info.class_name!r}, "
            f"rectangle={button.rectangle()}"
        )
    assert len(title_buttons) >= 2, "工程列表标题栏未定位到两个按钮"
    assert project_list.left_title_button() == title_buttons[0]
    assert project_list.right_title_button() == title_buttons[-1]

    controls = project_list.print_tree_controls()
    assert controls, "QTreeView 下没有获取到后代控件"
    tree_items = project_list.tree_items()
    assert tree_items, "QTreeView 下没有获取到 TreeItem 子控件"
    named_items = project_list.tree_items(named_only=True)
    names = [item.window_text() for item in named_items]
    print(f"有名称的工程树节点：{names}")
    assert named_items, "工程树下没有获取到有名称的节点"

    solution_name = names[0]
    assert project_list.solution_item(solution_name).exists()
    assert project_list.project_index_item(1).exists()
    assert project_list.locate("工程1").exists()
