"""Demo B: 回测引擎（脱离 yfinance，注入模拟数据）"""
import sys
sys.path.insert(0, r'e:\Projects\NDXinfo')

import numpy as np
import pandas as pd

from trading.sim_rules import SimExecutionRules
from trading.strategy import create_strategy
from indicators import calc_all_indicators
from backtest.engine import BacktestEngine
from backtest.reporter import ReportWriter
import tempfile, os, json

print('=== Demo B: BacktestEngine 端到端 ===')

# 构造明显上升趋势 + 一段回调，3 个标的
def synth(symbol, slope, noise=0.5):
    np.random.seed(hash(symbol) % (2**32))
    n = 250
    prices = np.linspace(100, 100 + slope * n, n) + np.random.normal(0, noise, n)
    df = pd.DataFrame({
        'Open': prices, 'High': prices + 0.6,
        'Low': prices - 0.6, 'Close': prices,
        'Volume': np.ones(n) * 1e6,
    })
    df.index = pd.date_range('2024-01-01', periods=n, freq='D')
    return calc_all_indicators(df)

data_map = {
    'NVDA': synth('NVDA', slope=1.0),
    'AAPL': synth('AAPL', slope=0.4, noise=1.0),
    'MSFT': synth('MSFT', slope=-0.2, noise=1.5),
}

# 用 ma_trend + 5 bps 滑点 + 每笔 $0.005
engine = BacktestEngine(
    df_by_symbol=data_map,
    strategy=create_strategy('ma_trend'),
    initial_cash=100000.0,
    rules=SimExecutionRules(slippage_bps=5, commission_per_share=0.005, min_commission=1.0),
)
res = engine.run()
m = res.metrics

print('strategy:    ' + res.strategy_name)
print('symbols:     ' + ', '.join(res.symbols))
print('period:      ' + str(res.start_ts) + ' -> ' + str(res.end_ts))
print('trades:      ' + str(len(res.portfolio.trades)))
print('total_return:' + format(m.total_return*100, '.2f') + '%')
print('annual:      ' + format(m.annual_return*100, '.2f') + '%')
print('max_drawdown:' + format(m.max_drawdown*100, '.2f') + '%')
print('sharpe:      ' + format(m.sharpe_ratio, '.3f'))
print('calmar:      ' + format(m.calmar_ratio, '.3f'))
print('profit_factor:' + format(m.profit_factor, '.3f'))
print('win_rate:    ' + format(m.win_rate*100, '.1f') + '%')
print('turnover:    ' + format(m.turnover, '.3f'))

# 写出报告（HTML + JSON + CSV）到临时目录，最后我们读 JSON 看一下
with tempfile.TemporaryDirectory() as td:
    rw = ReportWriter(res)
    jp = rw.write_json(os.path.join(td, 'bt.json'))
    payload = json.loads(open(jp, encoding='utf-8').read())
    print('\n[ReportWriter.write_json sample]:')
    print(json.dumps(payload['summary']['metrics'], indent=2, ensure_ascii=False)[:800])
    # 同样验证 HTML / CSV
    hp = rw.write_html(os.path.join(td, 'bt.html'))
    cp = rw.write_csv_trades(os.path.join(td, 'bt.csv'))
    print('\nfiles written:')
    print(' json bytes: ' + str(os.path.getsize(jp)))
    print(' html bytes: ' + str(os.path.getsize(hp)))
    print(' csv bytes:  ' + str(os.path.getsize(cp)))
