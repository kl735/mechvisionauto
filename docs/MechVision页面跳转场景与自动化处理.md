# MechVision 页面跳转场景与自动化处理

## 1. 文档目的

在 MechVision GUI 自动化过程中，点击按钮后不一定只是“进入新页面”。根据窗口层级、句柄和控件树的变化，目前实际遇到了四种不同场景。

如果没有区分这些场景，容易出现：

- 继续使用已经失效的窗口对象。
- 等待了错误的窗口。
- 在父窗口中查找实际属于 Popup 的控件。
- 页面已经切换，但仍然使用旧页面的控件。
- Popup 已经销毁，却继续使用旧 handle。

本文说明这四种场景的特征、判断方式和当前代码中的处理方法。

---

## 2. 场景一：旧顶层窗口消失，新顶层窗口出现

### 实际案例

```text
欢迎页面
  ↓ 点击“新建空白方案”
欢迎页面消失
  ↓
Mech-Vision 主窗口出现
```

### 窗口变化

- 欢迎窗口和主窗口是两个不同的顶层窗口。
- 窗口标题不同。
- 原生窗口 handle 不同。
- 原来的 `WelcomePage` 不能代表主窗口。
- 欢迎窗口可能被销毁，也可能先隐藏后销毁。

### 当前处理方式

首先通过 `WelcomePage` 点击按钮：

```python
welcome.create_empty_solution()
```

然后使用 Win32 等待新的主窗口：

```python
main_handle = wait_for_main_window(timeout=60)
```

最后使用新 handle 创建主窗口 Page：

```python
main_page = MainWindowPage.attach(main_handle)
```

### 为什么要重新定位

不能这样处理：

```python
welcome.create_empty_solution()
welcome.main_window.child_window(title="工程列表")
```

因为“工程列表”属于新的主窗口，不属于原来的欢迎窗口控件树。

### 推荐处理模板

```python
old_handle = welcome.main_window.handle
welcome.create_empty_solution()

new_handle = wait_for_main_window(timeout=60)
assert new_handle != old_handle

main_page = MainWindowPage.attach(new_handle)
```

### 核心原则

> 旧顶层窗口消失后，必须重新获取新窗口 handle，并创建新的 Page Object。

---

## 3. 场景二：父窗口保留，同时出现新的顶层窗口

### 实际案例

```text
Mech-Vision 主窗口
  ↓ 点击“配置向导”
主窗口仍然存在
  +
AI分类（正反/有无）配置向导出现
```

其他类似案例：

- 重命名模型对话框。
- 删除确认对话框。
- 标注图集窗口。
- 文件选择窗口。

### 窗口变化

- 父窗口仍然存在。
- 出现新的顶层窗口 handle。
- 新窗口通常和父窗口属于同一进程。
- 新窗口可能是普通窗口，也可能是模态窗口。
- 模态窗口出现后，父窗口通常暂时不能操作。

### 当前处理方式

点击“配置向导”后，以主窗口 handle 作为参考：

```python
page = AiClassificationConfigPage.wait_for_open(
    main_page.handle,
    timeout=30,
)
```

`wait_for_open()` 的处理逻辑：

1. 根据参考窗口 handle 获取 ProcessId。
2. 枚举该进程中的可见顶层窗口。
3. 读取每个窗口的 UIA 属性。
4. 同时校验标题、ClassName 和 AutomationId。
5. 找到后通过新 handle 创建配置向导 Page。

AI 分类配置向导使用的稳定属性：

```text
Name: AI分类（正反/有无）
ClassName: mmind::Dialog
AutomationId: mmind__Dialog
```

### 为什么使用参考窗口 handle

只按标题搜索可能定位到：

- 其他 Mech-Vision 进程的窗口。
- 上一次测试遗留的窗口。
- 标题相同但类型不同的窗口。

通过参考窗口获取 ProcessId，可以将搜索限制在当前 Mech-Vision 进程内。

### 推荐处理模板

```python
reference_hwnd = main_page.handle

click_open_dialog()

dialog_page = DialogPage.wait_for_open(
    reference_hwnd,
    timeout=10,
)
```

### 核心原则

> 父窗口保留时，不要覆盖父 Page；为新顶层窗口创建独立 Page Object。

---

## 4. 场景三：顶层窗口不变，只切换内部子页面

### 实际案例

```text
AI 分类默认配置页
  ↓ 点击“编辑”
目标区域编辑页
```

### 窗口变化

这个过程中：

- AI 分类配置向导 handle 不变。
- 顶层窗口标题不变。
- `QStackedWidget` 的 RuntimeId 可能不变。
- 当前可见的子页面发生变化。

观察到的页面 ClassName：

```text
默认配置页：mmind::QuickAiNavigator
目标区域页：mmind::QuickAiRoiEditor
```

### 当前处理方式

点击编辑按钮：

```python
self.target_region_edit_button().click_input()
```

继续使用原配置向导中的 `QStackedWidget`：

```python
editor = AiClassificationTargetRegionEditorPanel(
    self.config_panel(),
    timeout=self.timeout,
)
```

然后等待 `QStackedWidget` 的可见直接子控件变成：

```text
mmind::QuickAiRoiEditor
```

### 为什么不重新连接顶层窗口

顶层窗口没有变化，因此不需要：

```python
Application(backend="uia").connect(...)
```

重新连接不仅没有必要，还可能增加定位时间。

### 为什么不能只检查 RuntimeId

`QStackedWidget` 是页面容器。页面切换时容器本身没有变化，只是当前显示的子页面变化。

因此下面的判断不可靠：

```python
new_runtime_id != old_runtime_id
```

应该判断当前可见子页面：

```python
for child in stack_panel.children():
    if (
        child.element_info.class_name
        == "mmind::QuickAiRoiEditor"
        and child.is_visible()
    ):
        return child
```

### 推荐处理模板

```python
button.click_input()

panel = TargetEditorPanel(stack_widget)
panel.wait_for_visible()

return panel
```

### 核心原则

> 顶层窗口不变时，继续使用原 Page，只为新的内部页面创建 Panel 对象。

---

## 5. 场景四：出现短暂 Popup，随后出现模态确认窗口

### 实际案例

删除模型时的完整流程：

```text
AI 分类配置向导
  ↓ 右键模型
Qt Popup 菜单出现
  ↓ 点击“删除”
Popup 菜单立即消失
  ↓
删除确认窗口出现
  ↓ 点击“确定”或“取消”
确认窗口消失
  ↓
模型列表刷新
```

这不是一次简单的页面跳转，而是连续两个临时顶层窗口。

## 5.1 第一阶段：右键 Popup 菜单

Qt 右键菜单通常是独立顶层窗口，例如：

```text
Qt5152QWindowPopupSaveBits
```

菜单项包括：

```text
创建副本
重命名
删除
```

### 当前处理方式

1. 设置 Per-Monitor DPI Awareness。
2. 将配置向导设置为前台窗口。
3. 点击目标模型项，使其获得焦点。
4. 发送 `Shift+F10`。
5. 枚举同一进程中的可见顶层窗口。
6. 找到 ClassName 包含 `Popup` 的窗口。
7. 在 Popup 中定位对应 `MenuItem`。

示意代码：

```python
self.window.set_focus()
item.click_input()
keyboard.send_keys("+{F10}")

for hwnd in self._visible_process_windows():
    if "Popup" not in win32gui.GetClassName(hwnd):
        continue

    popup = Application(backend="uia").connect(handle=hwnd)
    menu_item = popup.window(handle=hwnd).child_window(
        title="删除",
        control_type="MenuItem",
    )
```

## 5.2 “存在时间短”是什么意思

Popup 只在下面这段时间存在：

```text
右键模型
  ↓
Popup 创建
  ↓
点击菜单项或点击其他位置
  ↓
Popup 立即销毁
```

它可能只存在几百毫秒到几秒。

需要注意：

- 右键之前无法定位它。
- 打开后必须立即查找。
- 点击菜单项后 Popup handle 会失效。
- 不能把 Popup Page 长期保存在实例属性中。
- 下次右键会创建新的 Popup 和新的 handle。
- 点击窗口其他位置或按 Esc，也会让 Popup 消失。

因此应该这样执行：

```python
打开右键菜单()
立即查找Popup()
立即点击菜单项()
```

不要这样执行：

```python
popup = 打开并缓存Popup()
# 执行很多其他操作
popup.click_delete()
```

因为执行到最后时，Popup 可能已经不存在。

## 5.3 第二阶段：删除确认窗口

点击 Popup 中的“删除”后：

- Popup 消失。
- 新的 `StyledMessageBox` 顶层窗口出现。
- 配置向导仍然存在，但暂时不能操作。
- 确认框会一直保留到用户点击按钮。

当前使用：

```python
message_box = MessageBoxPage.wait_for_open(
    reference_hwnd,
    timeout=self.timeout,
)
```

然后：

```python
message = message_box.message()
message_box.confirm()
```

或者：

```python
message_box.cancel()
```

### Popup 和确认窗口的区别

Popup：

- 存在时间短。
- 点击其他位置就会消失。
- 操作后 handle 立即失效。
- 通常用于菜单和下拉选项。

确认窗口：

- 会持续等待用户操作。
- 通常是模态窗口。
- 包含确定、取消等按钮。
- 操作完成后才销毁。

### 核心原则

> Popup 必须即时定位和操作；确认窗口则使用独立 MessageBoxPage 等待并处理。

---

## 6. 四种场景的统一判断流程

点击按钮后，可以按照以下顺序判断。

### 第一步：检查是否出现新的顶层窗口

记录操作前的窗口 handle：

```python
before_handles = visible_process_windows(process_id)
```

点击后重新获取：

```python
after_handles = visible_process_windows(process_id)
```

如果出现新 handle：

- 可能是新页面窗口。
- 可能是模态弹窗。
- 可能是 Popup。

进一步根据 ClassName、标题和 AutomationId 判断具体类型。

### 第二步：检查原窗口是否仍然存在

如果旧窗口消失：

- 属于场景一。
- 重新定位新顶层窗口。
- 创建新的 Page Object。

如果旧窗口仍存在且出现新窗口：

- 属于场景二或场景四。
- 保留原 Page。
- 为新窗口创建独立或临时 Page。

### 第三步：没有新 handle 时检查内部页面

如果顶层窗口和 handle 都没有变化：

- 检查当前可见子页面 ClassName。
- 检查选中的 Tab。
- 检查目标控件是否出现。

这通常属于场景三。

### 第四步：检查是否只是数据或状态刷新

如果既没有新窗口，也没有页面切换，可能只是：

- 模型数量变化。
- 文本变化。
- 按钮 Enabled 状态变化。
- 列表内容刷新。
- 状态从未完成变为已完成。

此时只需要等待具体状态，不要等待窗口。

---

## 7. Page Object 设计建议

根据窗口变化选择对象类型。

### 顶层窗口 Page

适用于：

- `WelcomePage`
- `MainWindowPage`
- `AiClassificationConfigPage`
- `CharacterRecognitionConfigPage`
- `MessageBoxPage`

特征：

- 有独立顶层 handle。
- 可以独立等待打开或关闭。

### 内部 Panel

适用于：

- `StepLibraryPage`
- `ProjectListPage`
- `ProjectEditorPage`
- `AiClassificationTargetRegionEditorPanel`

特征：

- 没有独立顶层 handle。
- 依赖所属主窗口或容器。
- 通过可见子页面判断当前状态。

### 临时 Popup

适用于：

- 右键菜单。
- ComboBox 下拉菜单。
- Tooltip。

特征：

- 每次操作时临时定位。
- 不长期缓存。
- 使用完成后立即丢弃对象。

---

## 8. 当前项目中的对应关系

### 场景一

```text
WelcomePage
  → MainWindowPage
```

处理方式：

```text
点击按钮 → 等待新主窗口 → 获取新 handle → attach
```

### 场景二

```text
MainWindowPage
  → AiClassificationConfigPage
```

处理方式：

```text
保留主窗口 → 枚举同进程窗口 → 校验窗口属性 → 创建配置 Page
```

### 场景三

```text
AiClassificationConfigPage
  → AiClassificationTargetRegionEditorPanel
```

处理方式：

```text
保留顶层窗口 → 检查 QStackedWidget 可见子页面
```

### 场景四

```text
模型项
  → Qt Popup
  → MessageBoxPage
```

处理方式：

```text
即时定位 Popup → 点击菜单项 → 等待确认框 → 确认或取消
```

---

## 9. 最终总结

当前遇到的四种窗口变化可以归纳为：

1. 旧窗口消失，新顶层窗口替换它。
2. 父窗口保留，出现新的独立顶层窗口。
3. 顶层窗口不变，只切换内部子页面。
4. 出现短暂 Popup，操作后再出现模态确认窗口。

对应处理原则：

```text
窗口替换       → 重新获取 handle，创建新 Page
新增独立窗口   → 保留父 Page，为子窗口创建独立 Page
内部页面切换   → 保留顶层 Page，定位当前可见 Panel
短暂 Popup     → 每次即时定位、即时操作、不缓存
```

自动化代码不能只看“界面视觉上是不是换了”，而应该检查：

- 顶层窗口 handle 是否变化。
- 原窗口是否仍存在。
- 是否出现新顶层窗口。
- ClassName 和 AutomationId 是否匹配。
- 当前可见子页面是否变化。
- Popup 是否已经被销毁。

只要先判断属于哪种窗口变化，再选择对应处理方式，页面跳转相关的定位和超时问题就会更容易排查。
