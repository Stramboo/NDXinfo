"""Demo E: 新策略 H (kdj / boll_width / ensemble) + 旧策略仍可用"""
import sys
sys.path.insert(0, r'e:\Projects\NDXinfo')

import numpy as np
import pandas as pd
from indicators import calc_all_indicators
from trading.strategy import create_strategy
from trading.sim_rules import SimExecutionRules
from backtest.engine import BacktestEngine

print('=== Demo E: 新旧策略对比（同一份合成数据） ===')

# 一段：先抑后扬的爬升行情，让多策略都至少产生信号
n = 200
np.random.seed(42)
walk = np.concatenate([
    np.linspace(0, -8, 50),
    np.linspace(-8, 0, 30),
    np.linspace(0, 30, 120),
]) + np.random.normal(0, 0.6, 200)
prices = 100 + walk

df = pd.DataFrame({
    'Open': prices, 'High': prices + 0.5,
    'Low': prices - 0.5, 'Close': prices,
    'Volume': np.ones(n) * 1e6,
})
df.index = pd.date_range('2024-01-01', periods=n, freq='D')
df = calc_all_indicators(df)
data_map = {'NVDA': df}

def run_one(name):
    res = BacktestEngine(
        df_by_symbol=data_map,
        strategy=create_strategy(name),
        initial_cash=100000.0,
        rules=SimExecutionRules(slippage_bps=3, commission_per_share=0.01, min_commission=1.0),
    ).run()
    return res

strategies = ['macd', 'rsi', 'ma_trend', 'bollinger', 'multi',  # 旧
              'kdj', 'boll_width', 'ensemble']                  # 新
print(f'{"strategy":<12} {"trades":>7} {"return":>9} {"maxdd":>9} {"sharpe":>8} {"pf":>7} {"win%":>6}')
print('-' * 64)
for s in strategies:
    r = run_one(s)
    m = r.metrics
    print(f'{s:<12} {len(r.portfolio.trades):>7} '
          f'{m.total_return*100:>8.2f}% {m.max_drawdown*100:>8.2f}% '
          f'{m.sharpe_ratio:>8.3f} {m.profit_factor:>7.2f} '
          f'{m.win_rate*100:>5.0f}%')

# 演示 contributors: ensemble 应报告多个子策略来源
r = run_one('ensemble')
last_sig_src = next(
    (t.reason for t in r.portfolio.trades if '加权综合' in t.reason),
    '(no ensemble trade)'
)
print('\nensemble 最近一笔 reason:')
print('  ' + last_sig_src)
