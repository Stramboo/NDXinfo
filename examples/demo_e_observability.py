"""Demo D: 结构化 JSON 日志 + SQLite 持久层 + 统计 CLI"""
import sys, os, tempfile, json, subprocess
sys.path.insert(0, r'e:\Projects\NDXinfo')

from trading.observability import setup_logging
from trading.persistence import SQLiteStore

print('=== Demo D: observability + persistence ===')

# D-1: JSON 日志（用子进程避免 Windows 文件句柄延迟释放）
print('\n[D-1] setup_logging(json_format=True) 写一行 JSON 日志 (subprocess)')
runner = os.path.join(os.path.dirname(__file__), 'demo_d1_log.py')
with tempfile.TemporaryDirectory() as td:
    code = (
        'import sys; sys.path.insert(0, r"e:\\Projects\\NDXinfo"); '
        'from trading.observability import setup_logging; '
        'import logging; setup_logging(level="INFO", log_dir=r"' + td.replace('\\','\\\\') + '", json_format=True); '
        'logger = logging.getLogger("demo"); '
        'logger.info("order filled", extra={"order_id":"o1","symbol":"AAPL","qty":10,"fill_price":180.5}); '
        'logger.warning("rate limit hit", extra={"yfinance_error":"too many requests","retry_in_s":30}); '
        'print("[d1] done")'
    )
    sub = os.path.join(td, 'd1_runner.py')
    with open(sub, 'w', encoding='utf-8') as f:
        f.write(code)
    out = subprocess.check_output([sys.executable, sub]).decode()
    print(out.strip())
    log_file = os.path.join(td, 'trader.log')
    lines = [l for l in open(log_file, encoding='utf-8').read().splitlines() if l.strip()]
    print('  total JSON lines: ' + str(len(lines)))
    print('  sample:')
    print('    ' + lines[0])
    parsed = json.loads(lines[0])
    print('  parsed.context keys: ' + str(sorted(parsed.get('context', {}).keys())))

# D-2/D-3: SQLite + stats CLI
print('\n[D-2] SQLiteStore 写入 4 张表')
with tempfile.TemporaryDirectory() as td:
    db = os.path.join(td, 'trader.db')
    store = SQLiteStore(db)
    store.insert_order(order_id='o1', symbol='AAPL', side='BUY',
                       quantity=10, price=180.5, commission=1.0, status='FILLED')
    store.insert_signal(symbol='AAPL', strategy='multi', action='BUY',
                        strength=0.7, reason='MACD cross', executed=1)
    store.insert_equity_snapshot(equity=100050.0, cash=81985.0,
                                  market_value=18065.0, daily_pnl=50.0)
    store.insert_error(level='ERROR', module='trading.executor',
                       msg='rate limit', traceback='Traceback...')
    counts = store.table_counts()
    print('  ' + json.dumps(counts))
    store.close()

    out = subprocess.check_output([
        sys.executable, '-m', 'trading.persistence', 'stats', '--db', db
    ]).decode()
    parsed = json.loads(out)
    print('\n[D-3] python -m trading.persistence stats:')
    print('  tables   = ' + json.dumps(parsed['tables']))
    print('  size_mb  = ' + str(parsed['db_size_mb']))
    print('  24h errs = ' + json.dumps(parsed['24h']['errors_by_level_24h']))
