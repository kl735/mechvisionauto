# MechvisionAuto

这个仓库是搭建 Mech-Vision 软件自动化测试框架的代码。测试通过界面操作软件，再用 Python SDK 核对方案、工程和步骤是否符合预期。

当前配套软件是 Mech-Vision 2.2.2-dev-10-27。

## 框架怎么分工

- 界面层负责能在界面上完成的操作：启动软件、点击欢迎页、搜索步骤库、把步骤拖到画布、选中工程、删除步骤。
- SDK 层负责打开和保存方案，并读取工程与步骤，用来做断言。
- 画布上的步骤是绘制出来的，没有独立控件。这类点击先用截图模板定位，再在匹配位置操作。

## 目录

- `pages/`：页面对象。欢迎页、最近使用和步骤库按控件的 `auto_id` 定位。
- `services/`：`VisionSdkClient`，封装 SDK 的初始化、打开方案、保存方案、读取工程和步骤。
- `utils/mech_vision_app.py`：启动或连接 Mech-Vision，测试结束时关闭本次启动的进程。
- `image_locator.py` 和 `templates/`：在窗口截图中匹配画布上的步骤标题。
- `conftest.py`：pytest 夹具。一次测试会话共用一个 Mech-Vision 进程。
- `控件文档/`：Inspect 导出的控件树，编写页面对象时对照使用。
- `说明文档.md`：本机环境、SDK 安装方式和各测试用例的操作细节。

## 运行

在项目根目录执行：

```powershell
pytest test_create_step.py
```

需要 Python 3.12、pytest，以及与当前 Mech-Vision 版本一致的 `mmind_vision`。安装路径和强制重装命令见 `说明文档.md`。
