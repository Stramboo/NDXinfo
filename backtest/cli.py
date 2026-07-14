# -*- coding: utf-8 -*-
"""
回测 CLI 入口：

    python -m backtest.cli --strategy multi --symbols NVDA --period 1y --out reports/bt.html

完全独立于 trader.py；不影响实盘 / GUI 行为。
"""

import argparse
import logging
import os
import sys
from datetime import datetime

import pandas as pd

from backtest.engine import BacktestEngine
from backtest.reporter import ReportWriter
from trading.sim_rules import SimExecutionRules
from trading.strategy import create_strategy

logger = logging.getLogger(__name__)


def _load_data(symbols: list[str], period: str) -> dict[str, pd.DataFrame]:
    """从 yfinance 加载历史数据（仅 CLI 路径联网）。"""
    import yfinance as yf
    out: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        df = yf.download(
            sym, period=period, interval="1d",
            auto_adjust=True, progress=False, repair=True,
        )
        if df is None or df.empty:
            logger.warning(f"无法获取 {sym} 历史数据，已跳过")
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.columns = [str(c).capitalize() for c in df.columns]
        out[sym.upper()] = df
    return out


def main(argv: list[str] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m backtest.cli",
        description="回测 CLI：策略 + 标的 + 周期 → HTML/JSON/CSV 报告",
    )
    parser.add_argument("--strategy", default="multi",
                        choices=["macd", "rsi", "ma_trend", "bollinger", "multi"],
                        help="策略名")
    parser.add_argument("--symbols", default="NVDA",
                        help="逗号分隔标的代码，如 NVDA,AAPL,MSFT")
    parser.add_argument("--period", default="1y",
                        help="yfinance period，例如 6mo / 1y / 2y / 5y")
    parser.add_argument("--cash", type=float, default=100000.0)
    parser.add_argument("--slippage-bps", type=float, default=1.0)
    parser.add_argument("--commission-per-share", type=float, default=0.0)
    parser.add_argument("--out", default=None,
                        help="输出报告路径（HTML），默认 reports/backtest_<runid>.html")
    parser.add_argument("--json", action="store_true", help="同时输出 JSON")
    parser.add_argument("--csv", action="store_true", help="同时输出 CSV")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    logger.info(f"开始回测: strategy={args.strategy} symbols={symbols} period={args.period}")

    df_map = _load_data(symbols, args.period)
    if not df_map:
        logger.error("没有可用的历史数据，退出")
        return 1

    rules = SimExecutionRules(
        slippage_bps=args.slippage_bps,
        commission_per_share=args.commission_per_share,
    )

    engine = BacktestEngine(
        df_by_symbol=df_map,
        strategy=create_strategy(args.strategy),
        initial_cash=args.cash,
        rules=rules,
    )
    result = engine.run()

    runid = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_html = args.out or f"reports/backtest_{args.strategy}_{runid}.html"
    out_json = out_html.replace(".html", ".json")
    out_csv = out_html.replace(".html", "_trades.csv")

    writer = ReportWriter(result)
    writer.write_html(out_html)
    logger.info(f"HTML 报告: {out_html}")
    if args.json:
        writer.write_json(out_json)
        logger.info(f"JSON 指标: {out_json}")
    if args.csv:
        writer.write_csv_trades(out_csv)
        logger.info(f"CSV 交易: {out_csv}")

    m = result.metrics
    print(
        f"\n=== 回测结果 ===\n"
        f"  strategy:  {result.strategy_name}\n"
        f"  symbols:   {', '.join(result.symbols)}\n"
        f"  period:    {result.start_ts} → {result.end_ts}\n"
        f"  total_ret: {m.total_return:.2%}\n"
        f"  annual:    {m.annual_return:.2%}\n"
        f"  max_dd:    {m.max_drawdown:.2%}\n"
        f"  sharpe:    {m.sharpe_ratio:.2f}\n"
        f"  calmar:    {m.calmar_ratio:.2f}\n"
        f"  pf:        {m.profit_factor:.2f}\n"
        f"  win_rate:  {m.win_rate:.2%}\n"
        f"  trades:    {m.trade_count}\n"
        f"  turnover:  {m.turnover:.2f}\n"
        f"  report:    {out_html}\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
