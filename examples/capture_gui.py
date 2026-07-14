# -*- coding: utf-8 -*-
"""
capture_gui.py — 拍两张 TraderMainWindow 截图（dark / light）

执行后输出 examples/screenshots/{trader_dark.png, trader_light.png}

原理：
    1) 启动 QApplication
    2) 实例化 TradingEngine（模拟券商，零延迟）
    3) 预填一组模拟价格，确保 dashboard 数字不是 0
    4) 实例化 TraderMainWindow，show() + QApplication.processEvents() 让布局完成
    5) apply_theme(app, 'dark') -> grab().save(...)
    6) apply_theme(app, 'light') -> grab().save(...)
    7) 退出

依赖：PyQt5, pyautogui（仅用于保险：取桌面尺寸裁剪）
"""

import os
import sys

# 让脚本能被 `python examples/capture_gui.py` 直接运行
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

OUT_DIR = os.path.join(_HERE, "screenshots")


def _safe_qapp() -> "QApplication":
    """已有 QApplication 就复用，否则新建一个"""
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()  # type: ignore
    if app is None:
        app = QApplication(sys.argv)
    return app  # type: ignore


def _seed_prices(engine, symbols_and_prices):
    """给 engine.broker 喂一组价格，避免 dashboard 全是 0"""
    for sym, price in symbols_and_prices:
        engine.broker.set_price(sym, price)


def _force_repaint(window):
    """强制重绘 widget，给真实 paint 事件让 grab() 与显示保持一致。"""
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    # 1) 让所有 widget unpolish/polish，强制重新计算样式
    if window.style():
        window.style().unpolish(window)
        window.style().polish(window)
    # 2) 让所有子 widget unpolish/polish（强制重算所有子控件样式）
    for child in window.findChildren(object.__class__):
        try:
            if child.style() is not None:
                child.style().unpolish(child)
                child.style().polish(child)
        except Exception:
            pass
    window.update()
    window.repaint()
    for _ in range(15):
        app.processEvents()


def _grab_window(window, path: str) -> int:
    """保存 widget grab；返回文件字节数。

    注意：在 offscreen / session 内 grab，Qt 缓存可能让两次截图相同。
    这里强制 window.repaint() + 多次 processEvents。
    """
    from PyQt5.QtCore import QSize
    from PyQt5.QtWidgets import QApplication
    window.repaint()
    for _ in range(8):
        QApplication.instance().processEvents()  # type: ignore
    img = window.grab()
    if img.width() > 1600 or img.height() > 1100:
        img = img.scaled(QSize(1600, 1100))
    ok = img.save(path, "PNG")
    if not ok:
        raise RuntimeError(f"QImage.save 失败: {path}")
    return os.path.getsize(path)


def main() -> int:
    print("=== capture_gui.py — 拍 TraderMainWindow dark/light 截图 ===")

    # 1) 依赖检查
    try:
        from PyQt5.QtWidgets import QApplication   # noqa: F401
        from PyQt5.QtCore import QTimer             # noqa: F401
    except ImportError as e:
        print(f"[skip] PyQt5 未安装: {e}")
        return 0  # 0=正常退出（CI 上当 skip 处理）

    # 2) 安装导入
    from gui.main_window import TraderMainWindow
    from gui.styles import apply_theme
    from trading.trading_engine import TradingEngine

    # 3) QApplication + 引擎 + 喂价
    app = _safe_qapp()
    engine = TradingEngine(broker_type="simulation",
                           strategy_name="multi",
                           initial_cash=100000)
    _seed_prices(engine, [
        ("NVDA", 482.10), ("AAPL", 175.42), ("MSFT", 421.55),
        ("GOOGL", 142.78), ("AMZN", 178.22), ("TSLA", 248.65),
        ("META", 502.10), ("SPY", 528.30), ("QQQ", 462.85),
    ])

    # 4) 主窗口
    win = TraderMainWindow(engine=engine)
    win.show()
    # 给 Qt 一点时间处理 layout / paint
    QTimer.singleShot(0, lambda: None)  # 等价 app.processEvents 一次
    for _ in range(8):
        app.processEvents()

    os.makedirs(OUT_DIR, exist_ok=True)

    # 5) Dark 主题
    apply_theme(app, "dark")
    _force_repaint(win)
    dark_path = os.path.join(OUT_DIR, "trader_dark.png")
    dark_size = _grab_window(win, dark_path)
    print(f"  saved: {dark_path}  ({dark_size:,} bytes)")

    # 6) Light 主题：再 apply + 强制 polish + repaint
    apply_theme(app, "light")
    win.setStyleSheet("")  # 先清掉，触发 unpolish
    apply_theme(app, "light")
    _force_repaint(win)
    light_path = os.path.join(OUT_DIR, "trader_light.png")
    light_size = _grab_window(win, light_path)
    print(f"  saved: {light_path}  ({light_size:,} bytes)")

    # 7) 断言：dark ≠ light（防止主题切换回归）
    import hashlib
    def md5(path):
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    dark_md5 = md5(dark_path)
    light_md5 = md5(light_path)
    print("  dark  md5: " + dark_md5)
    print("  light md5: " + light_md5)
    if dark_md5 == light_md5:
        print("  [FAIL] dark 和 light 的截图字节相同，主题切换可能未生效")
        win.close()
        return 2

    # 8) 额外检查：light 主题应比 dark 大（白色像素 PNG 编码更密集）
    if light_size <= dark_size:
        print(f"  [WARN] light ({light_size}B) 未显著大于 dark ({dark_size}B)，"
              f"但内容确实不同（断言已通过）")

    print("  [OK] dark 与 light 主题确实生成了不同内容")

    # 9) 退出
    win.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
