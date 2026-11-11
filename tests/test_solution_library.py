# coding: utf-8
"""验证欢迎窗口中的案例库页面封装。"""

from pages.welcome_page import WelcomePage


# def test_solution_library_panel(welcome_page: WelcomePage) -> None:
#     """验证进入案例库、读取案例信息并返回欢迎页。"""
#     library = welcome_page.create_from_library()

#     assert library.is_open()
#     assert library.title_label().is_visible()
#     assert library.search_edit().is_visible()
#     assert library.download_button().is_visible()
#     assert library.card_list().is_visible()
#     assert library.solution_name_edit().is_visible()
#     assert library.path_edit().is_visible()
#     assert library.docs_button().is_visible()
#     assert library.create_button().is_visible()

#     cards = library.card_items()
#     print(len(cards))

#     assert cards, "案例库中没有案例卡片"

#     solution_name = library.select_card(0)
#     print(f"第一个案例名称：{solution_name}")
#     assert solution_name.strip()

#     for category in ("应用模板", "教学示例", "典型案例"):
#         assert library.category_tab(category).is_visible()

#     library.select_category("教学示例", expected_subcategory="预处理")
#     for subcategory in ("预处理", "3D定位", "2D定位"):
#         assert library.subcategory_tab(subcategory).is_visible()

#     teaching_first_name = library.select_card(0)
#     print(f"教学示例-预处理第一个案例名称：{teaching_first_name}")
#     assert teaching_first_name.strip()
#     assert teaching_first_name != solution_name

#     library.select_subcategory("3D定位")
#     assert library.card_items(), "切换二级分类后没有案例卡片"
#     loc3d_first_name = library.select_card(0)
#     print(f"教学示例-3D定位第一个案例名称：{loc3d_first_name}")
#     assert loc3d_first_name.strip()
#     assert loc3d_first_name != teaching_first_name

#     library.select_category("典型案例", expected_subcategory="定位装配")
#     for subcategory in ("有序工件拣选", "定位装配", "无序工件拣选"):
#         assert library.subcategory_tab(subcategory).is_visible()

#     library.back_button().click_input()
#     welcome_page.create_empty_solution_button().wait(
#         "exists visible",
#         timeout=welcome_page.timeout,
#     )


def test_click_all_categories_and_print_first_case(
    welcome_page: WelcomePage,
) -> None:
    """依次点击全部一级、二级分类，并打印每个分类的首个案例名称。"""
    library = welcome_page.create_from_library()
    categories = {
        "应用模板": (),
        "教学示例": (
            "预处理",
            "3D定位",
            "2D定位",
            "深度学习",
            "3D位姿调整",
            "路径规划",
            "防错过滤",
            "逻辑判断",
            "功能",
            "其他",
        ),
        "典型案例": (
            "有序工件拣选",
            "无序工件拣选",
            "定位装配",
            "拆码垛",
            "其他",
        ),
    }

    for category, subcategories in categories.items():
        expected = subcategories[0] if subcategories else None
        library.select_category(
            category,
            expected_subcategory=expected,
        )
        if library.card_items():
            print(len(library.card_items()))
            first_name = library.select_card(0)
            print(f"一级分类[{category}]首个案例：{first_name}")
            assert first_name.strip()
        else:
            print(f"一级分类[{category}]没有案例")

        for subcategory in subcategories:
            library.select_subcategory(subcategory)
            if library.card_items():
                print(len(library.card_items()))
                first_name = library.select_card(0)
                print(
                    f"二级分类[{category}/{subcategory}]"
                    f"首个案例：{first_name}"
                )
                assert first_name.strip()
            else:
                print(
                    f"二级分类[{category}/{subcategory}]没有案例"
                )

    library.back_to_welcome()
