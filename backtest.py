# -*- coding: utf-8 -*-
"""
NASDAQ 每日分析报告 - 轻量级回测引擎
纯 pandas 实现，验证交易信号的历史表现
"""

import logging
import numpy as np
import pandas as pd
from config import BACKTEST_INITIAL_CAPITAL, BACKTEST_COMMISSION, BACKTEST_LOOKBACK

logger = logging.getLogger(__name__)


class BacktestEngine:
    """轻量级回测引擎 - 仅做多、固定仓位"""

    def __init__(self, initial_capital=BACKTEST_INITIAL_CAPITAL,
                 commission=BACKTEST_COMMISSION):
        self.initial_capital = initial_capital
        self.commission = commission

    def generate_daily_signals(self, df):
        """
        生成逐日交易信号
        返回 DataFrame 含 'signal' 列: 1=买入, -1=卖出, 0=持有
        策略组合: MACD金叉买入/死叉卖出 + RSI超卖买入/超买卖出
        """
        signals = pd.DataFrame(index=df.index)
        signals["signal"] = 0

        # MACD 金叉（DIF 上穿 DEA）
        macd_golden = (df["DIF"] > df["DEA"]) & (df["DIF"].shift(1) <= df["DEA"].shift(1))
        # MACD 死叉（DIF 下穿 DEA）
        macd_death = (df["DIF"] < df["DEA"]) & (df["DIF"].shift(1) >= df["DEA"].shift(1))

        # RSI 超卖（< 30）买入信号
        rsi_oversold = df["RSI"] < 30
        # RSI 超买（> 70）卖出信号
        rsi_overbought = df["RSI"] > 70

        # 威廉指标超卖（< -80）辅助买入
        wr_oversold = df["WR"] < -80
        # 威廉指标超买（> -20）辅助卖出
        wr_overbought = df["WR"] > -20

        # 综合信号
        signals.loc[macd_golden | rsi_oversold | wr_oversold, "signal"] = 1
        signals.loc[macd_death | rsi_overbought | wr_overbought, "signal"] = -1

        return signals

    def run(self, df, lookback=BACKTEST_LOOKBACK):
        """
        执行回测
        - 信号触发次日开盘价成交（避免未来函数）
        - 仅做多，满仓买入/清仓卖出
        - 含交易成本
        """
        if df is None or len(df) < 60:
            logger.warning("回测数据不足，至少需要60个交易日")
            return None

        # 截取回测区间
        df_bt = df.tail(min(lookback, len(df))).copy()

        # 生成信号
        signals = self.generate_daily_signals(df_bt)

        # 模拟交易
        position = 0  # 0=空仓, 1=满仓
        cash = self.initial_capital
        shares = 0
        trades = []
        equity_curve = []
        entry_price = 0
        entry_date = None

        for i in range(len(df_bt)):
            date = df_bt.index[i]
            close = df_bt["Close"].iloc[i]
            signal = signals["signal"].iloc[i]

            # 次日开盘价成交（从第2天开始）
            if i > 0 and signal != 0:
                open_price = df_bt["Open"].iloc[i] if "Open" in df_bt.columns else close

                # 买入信号且当前空仓
                if signal == 1 and position == 0:
                    cost = cash * (1 - self.commission)
                    shares = cost / open_price
                    cash = 0
                    position = 1
                    entry_price = open_price
                    entry_date = date
                    trades.append({
                        "date": date, "action": "BUY",
                        "price": round(open_price, 2), "shares": round(shares, 2)
                    })

                # 卖出信号且当前持仓
                elif signal == -1 and position == 1:
                    proceeds = shares * open_price * (1 - self.commission)
                    pnl = proceeds - (entry_price * shares)
                    pnl_pct = (open_price / entry_price - 1) * 100
                    holding_days = (date - entry_date).days if entry_date else 0
                    cash = proceeds
                    trades.append({
                        "date": date, "action": "SELL",
                        "price": round(open_price, 2),
                        "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2),
                        "holding_days": holding_days
                    })
                    shares = 0
                    position = 0
                    entry_price = 0
                    entry_date = None

            # 记录每日净值
            if position == 1:
                equity = shares * close
            else:
                equity = cash
            equity_curve.append({
                "date": date.strftime("%Y-%m-%d"),
                "equity": round(equity, 2),
                "close": round(close, 2)
            })

        # 计算关键指标
        equity_series = pd.Series([e["equity"] for e in equity_curve])
        close_series = pd.Series([e["close"] for e in equity_curve])

        total_return = (equity_series.iloc[-1] / self.initial_capital - 1) * 100
        benchmark_return = (close_series.iloc[-1] / close_series.iloc[0] - 1) * 100

        # 最大回撤
        peak = equity_series.expanding().max()
        drawdown = (equity_series - peak) / peak * 100
        max_drawdown = drawdown.min()

        # 年化收益率（假设252交易日）
        trading_days = len(equity_series)
        if trading_days > 0:
            annual_return = ((equity_series.iloc[-1] / self.initial_capital) **
                             (252 / trading_days) - 1) * 100
        else:
            annual_return = 0

        # 夏普比率（简化：无风险利率2%）
        daily_returns = equity_series.pct_change().dropna()
        if len(daily_returns) > 1 and daily_returns.std() > 0:
            sharpe = (daily_returns.mean() - 0.02 / 252) / daily_returns.std() * np.sqrt(252)
        else:
            sharpe = 0

        # 胜率
        sell_trades = [t for t in trades if t["action"] == "SELL"]
        wins = [t for t in sell_trades if t.get("pnl", 0) > 0]
        win_rate = (len(wins) / len(sell_trades) * 100) if sell_trades else 0

        # 平均持仓天数
        holding_days_list = [t.get("holding_days", 0) for t in sell_trades]
        avg_holding = (sum(holding_days_list) / len(holding_days_list)) if holding_days_list else 0

        result = {
            "equity_curve": equity_curve,
            "trades": trades,
            "metrics": {
                "total_return": round(total_return, 2),
                "annual_return": round(annual_return, 2),
                "benchmark_return": round(benchmark_return, 2),
                "max_drawdown": round(max_drawdown, 2),
                "sharpe_ratio": round(sharpe, 2),
                "win_rate": round(win_rate, 1),
                "num_trades": len(sell_trades),
                "avg_holding_days": round(avg_holding, 1),
                "final_equity": round(equity_series.iloc[-1], 2),
            }
        }

        logger.info(f"回测完成: 总收益={total_return:.2f}%, 基准={benchmark_return:.2f}%, "
                     f"最大回撤={max_drawdown:.2f}%, 胜率={win_rate:.1f}%, 交易次数={len(sell_trades)}")

        return result
