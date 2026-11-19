# coding: utf-8
"""修改教学示例子分组名称，并验证本地 library_group.json。"""

from utils.solution_library_resources import (
    library_categories,
    rename_library_subgroup,
)

GROUP_NAME = "教学示例"
OLD_SUBGROUP_NAME = "预处理"
NEW_SUBGROUP_NAME = "新的子分组名称"


def main() -> None:
    renamed = rename_library_subgroup(
        GROUP_NAME,
        OLD_SUBGROUP_NAME,
        NEW_SUBGROUP_NAME,
    )
    assert renamed, (
        f"没有找到子分组：{GROUP_NAME}/{OLD_SUBGROUP_NAME}"
    )

    category = next(
        (
            item
            for item in library_categories()
            if item["name"] == GROUP_NAME
        ),
        None,
    )
    assert category is not None, f"没有找到一级分组：{GROUP_NAME}"

    subgroup_names = [
        subgroup["name"]
        for subgroup in category["subgroups"]
    ]
    assert NEW_SUBGROUP_NAME in subgroup_names, (
        f"子分组名称修改失败：{subgroup_names}"
    )
    assert OLD_SUBGROUP_NAME not in subgroup_names, (
        f"仍存在旧子分组名称：{subgroup_names}"
    )
    print(
        f"修改成功：{GROUP_NAME}/{OLD_SUBGROUP_NAME}"
        f" -> {NEW_SUBGROUP_NAME}"
    )


if __name__ == "__main__":
    main()
