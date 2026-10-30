# coding: utf-8
"""用 Inspect 属性定位 Mech-Vision 主窗口，并打印控件树。"""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from pywinauto import Application, Desktop


EXE_PATH = Path(
    r"D:\project\Mech-Vision & Mech-Viz-2.2.2-dev-10-20\Mech-Vision\mmind_vision.exe"
)
STARTUP_TIMEOUT = 60
DUMP_PATH = Path(__file__).resolve().parent / "主窗口控件文档.md"


def find_main_native_window(process_id: int):
    """在同名窗口里选出 Mech-Vision 主窗口，排除 Qt 弹层。"""
    windows = Desktop(backend="win32").windows(
        process=process_id,
        title_re=r".*Mech-Vision.*",
    )
    candidates = [
        window
        for window in windows
        if "QWindowPopup" not in window.class_name()
    ]
    icon_windows = [
        window
        for window in candidates
        if window.class_name() == "Qt5152QWindowIcon"
    ]
    pool = icon_windows or candidates
    if not pool:
        raise RuntimeError("未找到 Mech-Vision 主窗口")
    return max(
        pool,
        key=lambda window: window.rectangle().width() * window.rectangle().height(),
    )


def test_print_main_window_identifiers() -> None:
    """按 auto_id / class_name / title 定位主窗口，再打印控件标识。"""
    try:
        app = Application(backend="win32").connect(
            path=str(EXE_PATH),
            timeout=5,
        )
    except Exception:
        app = Application(backend="win32").start(
            f'"{EXE_PATH}"',
            work_dir=str(EXE_PATH.parent),
            timeout=STARTUP_TIMEOUT,
            wait_for_idle=False,
        )

    # Win32 取句柄后再切 UIA，避免按 auto_id 全树搜索卡死
    native_win = find_main_native_window(app.process)
    app = Application(backend="uia").connect(handle=native_win.handle)

    # 定位 Mech-Vision 主窗口（Inspect：auto_id=mainWindow）
    mech_win = app.window(handle=native_win.handle)
    mech_win.wait("exists", timeout=STARTUP_TIMEOUT)

    info = mech_win.element_info
    if (
        info.automation_id != "mainWindow"
        or info.class_name != "mmind::tailor_impl::TFramelessWindow"
        or "Mech-Vision" not in (info.name or "")
        or info.control_type != "Window"
    ):
        raise RuntimeError(
            "窗口属性与 Inspect 不一致："
            f" auto_id={info.automation_id!r}"
            f" class_name={info.class_name!r}"
            f" title={info.name!r}"
            f" control_type={info.control_type!r}"
        )

    print("窗口定位成功：", mech_win.window_text())
    print("auto_id：", info.automation_id)
    print("class_name：", info.class_name)
    print("control_type：", info.control_type)

    print("开始 print_control_identifiers() ...")
    buffer = StringIO()
    with redirect_stdout(buffer):
        mech_win.print_control_identifiers()
    text = buffer.getvalue()
    DUMP_PATH.write_text(text, encoding="utf-8")
    print(text)
    print(f"已写入 {DUMP_PATH}，共 {len(text.splitlines())} 行")


if __name__ == "__main__":
    test_print_main_window_identifiers()
