#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
美股自动交易系统 - 主入口

使用方法:
    python trader.py                      # 默认模拟模式，$100,000初始资金
    python trader.py --broker alpaca      # 使用 Alpaca（需设置API Key环境变量）
    python trader.py --cash 50000         # 模拟模式，$50,000初始资金
    python trader.py --strategy macd      # 使用 MACD 策略
    python trader.py --no-gui             # 纯命令行模式（无GUI）
"""

import sys
import os
import argparse
import logging

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def run_gui(args):
    """启动图形界面"""
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt

    # 高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 初始化交易引擎
    from trading.trading_engine import TradingEngine
    engine = TradingEngine(
        broker_type=args.broker,
        strategy_name=args.strategy,
        initial_cash=args.cash,
    )

    # 创建主窗口
    from gui.main_window import TraderMainWindow
    window = TraderMainWindow(engine=engine)
    window.show()

    sys.exit(app.exec_())


def run_cli(args):
    """纯命令行模式"""
    from trading.trading_engine import TradingEngine

    engine = TradingEngine(
        broker_type=args.broker,
        strategy_name=args.strategy,
        initial_cash=args.cash,
    )

    print("=" * 60)
    print(f"  美股自动交易系统 - 命令行模式")
    print(f"  券商: {engine.broker.name}")
    print(f"  策略: {engine.strategy.name}")
    print(f"  初始资金: ${args.cash:,.0f}")
    print("=" * 60)

    # 加载数据
    print("\n正在加载历史数据...")
    engine._load_all_history()

    # 显示账户
    status = engine.get_status()
    account = status["account"]
    print(f"\n账户状态:")
    print(f"  总资产:     ${account['equity']:,.2f}")
    print(f"  可用现金:   ${account['cash']:,.2f}")
    print(f"  持仓数量:   {len(status['positions'])}")

    if args.auto:
        print(f"\n启动自动交易（间隔 {args.interval} 秒）...")
        engine.start_auto(interval_seconds=args.interval)
        try:
            import time
            while True:
                time.sleep(5)
                status = engine.get_status()
                positions = status["positions"]
                print(f"\r[{status['timestamp']}] "
                      f"资产=${status['account']['equity']:,.0f} "
                      f"持仓={len(positions)} "
                      f"收益率={status['account']['total_return_pct']:+.2f}%", end="")
        except KeyboardInterrupt:
            print("\n\n正在停止...")
            engine.stop()
            print("已停止。")

    # 显示最终状态
    final = engine.get_status()
    print(f"\n最终状态:")
    print(f"  总资产:   ${final['account']['equity']:,.2f}")
    print(f"  收益率:   {final['account']['total_return_pct']:+.2f}%")


def main():
    parser = argparse.ArgumentParser(
        description="美股自动交易系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python trader.py                              # GUI 模拟模式
  python trader.py --no-gui --auto              # CLI 自动交易
  python trader.py --broker simulation --cash 100000  # 模拟 $100k
  python trader.py --strategy macd             # MACD 策略
  python trader.py --broker alpaca             # Alpaca 实盘/模拟
        """,
    )
    parser.add_argument("--broker", type=str, default="simulation",
                        choices=["simulation", "alpaca"],
                        help="券商类型 (默认: simulation)")
    parser.add_argument("--strategy", type=str, default="multi",
                        choices=["macd", "rsi", "ma_trend", "bollinger", "multi",
                                 "kdj", "boll_width", "ensemble"],
                        help="交易策略 (默认: multi)")
    parser.add_argument("--cash", type=float, default=100000.0,
                        help="模拟券商初始资金 (默认: 100000)")
    parser.add_argument("--no-gui", action="store_true",
                        help="纯命令行模式，不启动GUI")
    parser.add_argument("--auto", action="store_true",
                        help="启动后自动开始交易 (仅CLI模式)")
    parser.add_argument("--interval", type=int, default=60,
                        help="自动交易扫描间隔秒数 (默认: 60)")

    args = parser.parse_args()

    if args.no_gui:
        run_cli(args)
    else:
        run_gui(args)


if __name__ == "__main__":
    main()
