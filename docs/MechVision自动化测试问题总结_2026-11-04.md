# MechVision PC 端自动化测试问题总结

日期：2026-11-04

## 1. 当前项目进展

今天已经从零搭建出了一个可以运行的 MechVision GUI 自动化测试框架，当前主要结构如下：

```text
MechvisionAuto/
├── pages/                 # Page Object：窗口和控件定位、页面操作
├── services/              # Mech-Vision SDK 业务封装
├── tests/                 # pytest 自动化测试
│   └── config_wizard/     # 配置向导测试
├── utils/                 # 程序启动、窗口、图像定位等公共工具
├── conftest.py            # pytest 公共 fixture
└── pytest.ini             # pytest 配置
```

目前已完成的主要能力：

- 启动或连接 Mech-Vision。
- 定位欢迎页和主窗口。
- 将主窗口拆分为工程列表、步骤库和工程编辑区 Page。
- 打开指定方案并选择指定工程。
- 定位并打开 AI 分类配置向导。
- 封装 AI 字符识别、AI 分类配置向导。
- 新建、重命名和删除模型。
- 处理 Qt 右键菜单和删除确认弹窗。
- 定位目标区域编辑页面及其基础控件。
- 完成第一批 7 条 AI 分类 pytest 用例。

## 2. MechVisionApp 应该负责什么

### 遇到的问题

最初考虑把程序启动、主窗口定位、欢迎页定位、页面控件定位等功能都放进 `MechVisionApp`。

这样会造成：

- 类职责过多。
- 启动逻辑和页面控件逻辑互相耦合。
- 后续增加配置向导、弹窗时，`MechVisionApp` 会越来越复杂。

### 当前结论

`MechVisionApp` 只负责应用进程生命周期：

- 已启动时使用 `Application.connect()`。
- 未启动时使用 `Application.start()`。
- 测试结束时关闭由测试管理的程序。

窗口和控件定位分别放入对应的 Page Object：

- `WelcomePage`
- `MainWindowPage`
- `AiClassificationConfigPage`
- `CharacterRecognitionConfigPage`
- `MessageBoxPage`

### 后续需要改进

当前 `MechVisionApp.close()` 会直接调用 `kill()`。如果测试只是连接了用户已经打开的程序，也会将其关闭。

建议后续增加：

```python
self.started_by_test = True
```

只有测试真正启动了程序时才在 teardown 中关闭，避免误杀用户手动打开的 Mech-Vision。

## 3. 程序已启动不等于界面已准备好

### 遇到的问题

进程已经存在，但是主窗口或配置向导仍然定位失败，最后触发：

```text
pywinauto.timings.TimeoutError: timed out
```

### 原因

程序启动包含多个阶段：

1. 进程创建。
2. 欢迎窗口出现。
3. 方案加载。
4. 主窗口出现。
5. Qt 控件完成创建。
6. UIA 控件树可以访问。

进程存在只能证明第一步成功，不能证明后面的窗口已经准备完成。

### 解决方案

分别等待不同状态：

- `Application.is_process_running()`：进程是否运行。
- Win32 顶层窗口：主窗口是否创建。
- `window.wait("exists visible")`：窗口是否可见。
- UIA Page Object：窗口内部控件是否加载。

不要在启动函数中直接假设主窗口立即存在。

## 4. 顶层窗口采用 Win32，内部控件采用 UIA

### 遇到的问题

使用 `Desktop(backend="uia")` 全桌面搜索顶层窗口速度慢，而且容易扫描到无关窗口。

### 当前采用的定位链路

1. 使用 Win32 快速定位顶层窗口。
2. 获取原生窗口句柄 `handle`。
3. 使用该句柄连接 UIA。
4. 使用 UIA 定位按钮、文本框、列表等内部控件。

示意代码：

```python
native_window = win32_app.window(title="Mech-Vision")
handle = native_window.handle

uia_app = Application(backend="uia").connect(handle=handle)
main_window = uia_app.window(handle=handle)
```

这种方式兼顾了：

- Win32 顶层窗口定位速度。
- UIA 内部控件语义化定位能力。

## 5. WelcomePage、MainWindowPage 和子区域 Page 的关系

### 遇到的问题

主窗口中同时包含：

- 步骤库
- 工程列表
- 工程编辑区
- 步骤参数
- 可视化区域

不确定这些区域是否都应该写进一个 Page 类。

### 当前架构

`MainWindowPage` 作为主窗口容器，通过组合持有子区域：

```python
self.step_library = StepLibraryPage(main_window, timeout)
self.project_list = ProjectListPage(main_window, timeout)
self.project_editor = ProjectEditorPage(main_window, timeout)
```

设计原则：

- `MainWindowPage` 负责主窗口级操作。
- 子 Page 负责各自区域。
- 子 Page 不再重复连接主窗口。
- 配置向导等独立顶层窗口使用独立 Page。

这是组合关系，不是继承关系。

## 6. `@classmethod`、`@property` 和 `set_focus()`

### `@classmethod`

`@classmethod` 不是静态方法。

它接收的第一个参数是类本身 `cls`，适合实现：

```python
MainWindowPage.attach(...)
WelcomePage.attach(...)
AiClassificationConfigPage.wait_for_open(...)
```

`@staticmethod` 不会自动接收类或实例。

### `@property`

`@property` 将方法包装成属性访问：

```python
page.handle
```

而不是：

```python
page.handle()
```

适合句柄、标题等只读信息。

### `set_focus()`

`set_focus()` 将窗口切换到前台并让它接收键盘输入。

它对以下操作很重要：

- `Shift+F10`
- `Delete`
- `F1`
- 方向键
- `Ctrl+C`、`Ctrl+V`

窗口可见不代表它拥有键盘焦点。

## 7. QStackedWidget 及配置页面切换

### QStackedWidget 是什么

`QStackedWidget` 是 Qt 的堆叠页面容器，同一时间只显示其中一个子页面。

点击“编辑”后：

- 外层窗口句柄不变。
- `QStackedWidget` 的 RuntimeId 可能不变。
- 当前显示的子页面发生变化。

AI 配置向导中观察到：

- 默认配置页：`mmind::QuickAiNavigator`
- 目标区域编辑页：`mmind::QuickAiRoiEditor`

### 正确判断方式

不要只依赖：

- 窗口句柄
- RuntimeId
- 第一个文本

应检查 `QStackedWidget` 当前可见的直接子控件 ClassName。

## 8. AI 分类不应该继承字符识别配置 Page

### 遇到的问题

`AiClassificationConfigPage` 曾经继承：

```python
CharacterRecognitionConfigPage
```

### 为什么不合适

两者只是部分功能相似，并不是严格的“is-a”关系。

继承会让 AI 分类错误暴露字符识别专用功能，例如：

- 识别对象
- 拼接间隔符
- 字符尺寸
- 字符识别专用目标区域选项

### 当前处理

`AiClassificationConfigPage` 已改为独立 Page 类，包含：

- 模型列表操作。
- OK/NG 标注按钮。
- 高级设置。
- 置信度阈值。
- 热力图。
- 图像判定方式。
- AI 分类专用目标区域编辑页面。

### 后续建议

当前两个 Page 存在模型管理代码重复。以后可以使用组合方式抽取：

```python
self.models = ModelListPanel(window)
```

不要再让两个业务 Page 互相继承。

## 9. Qt Popup 右键菜单定位

### 遇到的问题

模型右键后出现“创建副本、重命名、删除”，这些菜单不一定属于配置向导 UIA 子树。

### 原因

Qt 菜单通常是独立顶层 Popup 窗口，例如：

```text
Qt5152QWindowPopupSaveBits
```

因此不能只使用：

```python
config_window.child_window(...)
```

### 当前解决方案

1. 选中模型项。
2. 发送 `Shift+F10` 打开右键菜单。
3. 枚举同一进程的可见顶层窗口。
4. 找到 ClassName 包含 `Popup` 的窗口。
5. 使用 UIA 定位 `MenuItem`。

## 10. 多显示器和 DPI 缩放导致点击偏移

### 实际现象

配置向导位于第二块显示器时，UIA 返回的控件矩形与实际鼠标坐标不一致。

例如代码要求点击：

```text
(3291, 372)
```

实际鼠标到达的位置却发生偏移，导致：

- 模型项没有获得焦点。
- `Shift+F10` 没有发送给目标模型。
- 删除和重命名菜单无法打开。
- 测试连续等待 30 秒后超时。

### 原因

不同显示器的 DPI 缩放比例不同，而测试进程未使用 Per-Monitor DPI Awareness。

### 当前解决方案

新增：

```python
set_per_monitor_dpi_awareness()
```

使用：

```python
SetThreadDpiAwarenessContext(PER_MONITOR_AWARE_V2)
```

并在 GUI 操作前设置当前线程 DPI 上下文。

另外，配置向导测试会将主窗口和配置窗口移动到主屏幕，以提高坐标操作稳定性。

## 11. UIA 能看到列表，但列表项文本可能为空

### 遇到的问题

AI 分类模型列表能够定位到 `ListItem`，但是：

```python
item.window_text()
```

返回空字符串。

### 原因

Qt 自定义列表项没有将模型名称正确暴露给 UIA Name 属性。

### 当前验证方式

- 通过模型数量变化验证新建和删除。
- 通过重命名弹窗中的 Edit 控件读取名称。
- 不直接依赖 ListItem 的 `window_text()`。

## 12. 自定义流程画布和 ROI 不完全支持 UIA

### 遇到的问题

UI Spy 无法定位部分流程画布、Step 或 ROI，但界面上确实存在这些对象。

### 原因

Qt 自定义绘制区域通常不会将内部图形对象暴露为标准 UIA 控件。

例如：

- Step 流程图。
- 矩形 ROI。
- 圆形 ROI。
- 多边形屏蔽区域。
- ROI 锚点。

### 当前策略

- 普通按钮、列表、文本优先使用 UIA。
- 自定义画布使用固定方案下的窗口比例坐标。
- 需要视觉结果验证时使用截图或 OpenCV。
- 业务结果优先通过 SDK 或输出数据断言。

坐标测试必须固定：

- 分辨率。
- DPI。
- 窗口大小。
- 方案布局。
- 测试数据。

## 13. 配置向导入口定位的误匹配

### 遇到的问题

使用截图文字匹配定位 Step 时，最高匹配结果可能落在日志或其他区域，而不是目标 Step。

错误点击后：

- Step 没有选中。
- 右侧步骤参数没有加载。
- 点击“配置向导”没有效果。
- 最终等待配置窗口超时。

### 当前解决方案

当前测试针对指定方案：

```text
step_name_assert_solution
```

方案布局固定，因此采用主窗口内的相对坐标选择目标 Step，再点击右侧步骤参数中的配置向导。

这能保证当前方案稳定运行，但它不是通用方案。

### 后续改进方向

- 给 Step 生成更稳定的局部模板。
- 将搜索范围限制在工程画布。
- 使用 SDK 获取 Step 信息，同时结合画布区域定位。
- 如果产品后续暴露 Step 的 UIA 属性，应切回 UIA 定位。

## 14. 测试方案被污染

### 实际问题

模型新建成功后，删除操作因为焦点和 DPI 问题失败，测试模型没有清理。

多次执行后模型数量达到 5，后续点击“新建”不再增加，导致：

```text
点击“新建”后模型数量没有增加
```

### 原因

测试直接操作了基准方案，并且 teardown 清理失败。

### 当前解决方案

每次测试会话开始时：

1. 复制指定方案。
2. 在 pytest 临时目录中打开副本。
3. 所有新建、重命名和删除都发生在副本中。
4. 原始方案保持不变。

这是 GUI 自动化测试的重要原则：

> 测试不能依赖上一次执行留下的状态，也不能污染基准数据。

## 15. pytest 与 conftest 的理解

### conftest.py 的作用

`conftest.py` 用于定义 pytest fixture。

它不是“全局函数文件”，而是根据目录层级自动发现：

- 根目录 `conftest.py` 可作用于其子目录。
- 子目录可以添加自己的 `conftest.py`。
- fixture 只有被测试参数引用或声明为 `autouse=True` 时才执行。

### 测试发现规则

pytest 默认识别：

- `test_*.py`
- `test_*()` 函数
- `Test*` 测试类

测试函数不需要手动写 `@pytest`。

装饰器主要用于：

- `@pytest.fixture`
- `@pytest.mark.parametrize`
- `@pytest.mark.smoke`
- `@pytest.mark.skip`

### 如何终止测试

终端中使用：

```text
Ctrl+C
```

如果 GUI 操作卡住，需要确认是否有模态弹窗正在阻塞主窗口。

## 16. 测试目录应该按业务模块划分

当前推荐结构：

```text
tests/
├── conftest.py
├── main_window/
├── step_library/
└── config_wizard/
    ├── conftest.py
    ├── test_ai_classification_basic.py
    ├── test_ai_classification_settings.py
    └── test_character_recognition.py
```

划分原则：

- 按业务模块划分。
- 不按照 Page 类一比一创建测试文件。
- Page 负责操作，测试负责断言。
- 冒烟、回归、硬件等类型使用 pytest marker。

## 17. 自动化可行性评估

AI 分类测试用例原始记录共 191 条，已经生成：

```text
AI分类测试用例_自动化评估.csv
```

评估结果：

- 推荐自动化：48 条，占 25.1%。
- 条件自动化：76 条，占 39.8%。
- 暂不自动化：67 条，占 35.1%。

保守估计，第一阶段适合稳定落地的自动化比例约为 30%～40%。

适合优先自动化：

- 窗口和页面切换。
- 按钮可用状态。
- 文本和提示。
- 模型新建、重命名和删除。
- 参数输入和边界值。
- 普通确认弹窗。

需要条件自动化：

- 虚拟相机。
- 固定图像。
- 训练和推理。
- Pose 输入。
- 截图比较。

暂不建议普通回归自动化：

- 真实相机。
- 加密狗人工插拔。
- 6 亿像素性能场景。
- 复杂 ROI 拖拽、旋转和锚点编辑。
- 没有量化标准的主观视觉判断。

## 18. 当前完成的 AI 分类测试

测试文件：

```text
tests/config_wizard/test_ai_classification_basic.py
```

当前覆盖：

- `M85028_0673`：模型列表显示。
- `M85028_0674`：新建模型。
- `M85028_0677`：模型重命名。
- `M85028_0678`：删除模型确认提示。
- `M85028_0679`：确认删除模型。
- `M85028_0680`：取消删除模型。
- `M85028_0700`：进入目标区域编辑页面。
- AI 分类默认页面核心控件冒烟检查。

最终执行结果：

```text
7 passed in 32.42s
```

## 19. 当前仍存在的风险

### 临时方案路径

当前默认方案路径位于 pytest 临时目录：

```text
C:\Users\mech-mind\AppData\Local\Temp\pytest-of-mech-mind\...
```

该目录可能被 pytest 自动清理。

目前支持通过环境变量覆盖：

```text
MECHVISION_AI_SOLUTION_PATH
```

后续应该将基准方案放入固定测试数据目录。

### 固定坐标依赖

配置向导入口目前依赖指定方案中的固定画布布局和窗口比例。

如果以下内容变化，定位可能失效：

- Step 被移动。
- 窗口比例变化。
- 方案布局变化。
- 产品 UI 布局变化。

### 公共代码重复

AI 字符识别和 AI 分类都包含模型管理逻辑，后续适合抽取 `ModelListPanel` 组合组件。

### 测试关闭程序

根目录 fixture 最终可能直接结束 Mech-Vision 进程，需要增加“是否由测试启动”的状态判断。

## 20. 下一步建议

建议按照以下顺序继续：

1. 将测试基准方案迁移到固定路径。
2. 改进 `MechVisionApp`，只关闭测试启动的进程。
3. 抽取公共 `ModelListPanel`。
4. 增加高级设置展开和收起测试。
5. 增加置信度最小值、中间值、最大值和非法值测试。
6. 增加“全部为 OK”和“至少一个为 OK”判定方式测试。
7. 增加热力图开关测试。
8. 增加标注状态和按钮可用状态测试。
9. 准备固定虚拟相机数据后实现采集和推理测试。
10. 最后再处理复杂 ROI 和真实硬件场景。

## 21. 总结

今天遇到的问题主要不是 Python 语法问题，而是企业级桌面 GUI 自动化常见的工程问题：

- 进程状态与 UI 状态不同步。
- Win32、UIA 和 Qt 自定义控件能力不同。
- 顶层窗口、Popup 和模态窗口属于不同窗口层级。
- 多显示器 DPI 会造成真实坐标偏移。
- 自定义画布无法完全依赖 UIA。
- 测试必须隔离数据并清理状态。
- Page Object 应通过组合划分职责。
- 自动化范围需要根据稳定性和维护成本选择。

目前框架已经具备继续扩展的基础，下一阶段应优先提高测试数据稳定性和 Page 公共组件复用能力，而不是立即追求覆盖所有 GUI 用例。
