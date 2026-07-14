"""Demo C: 配置外部化（YAML 加载 + 环境变量覆盖 + 热加载回调）"""
import sys, os, tempfile, threading, time
sys.path.insert(0, r'e:\Projects\NDXinfo')

from trading.config_loader import load_config, apply_env_overrides
from trading.hot_reload import FileWatcher

print('=== Demo C: AppConfig 加载 + env 覆盖 + FileWatcher ===')

# C-1: 直接加载 default.yaml
print('\n[C-1] load_config() 无参数 (默认 config/default.yaml)')
cfg = load_config()
print('  broker.type             = ' + cfg.broker.type)
print('  broker.initial_cash     = $' + format(cfg.broker.initial_cash, ',.0f'))
print('  risk.stop_loss_pct      = ' + format(cfg.risk.stop_loss_pct, '.1f') + '%')
print('  risk.cooldown_seconds   = ' + str(cfg.risk.cooldown_seconds) + 's')
print('  sim_rules.t_plus_one    = ' + str(cfg.sim_rules.t_plus_one))
print('  indicators.ma_periods   = ' + str(list(cfg.indicators.ma_periods)))

# C-2: 环境变量覆盖
print('\n[C-2] env 覆盖: NDX_RISK__STOP_LOSS_PCT=-12.5, NDX_SIM_RULES__SLIPPAGE_BPS=3')
os.environ['NDX_RISK__STOP_LOSS_PCT']  = '-12.5'
os.environ['NDX_SIM_RULES__SLIPPAGE_BPS'] = '3'
os.environ['NDX_BROKER__INITIAL_CASH'] = '250000'
cfg2 = apply_env_overrides(cfg)
print('  risk.stop_loss_pct (改) = ' + format(cfg2.risk.stop_loss_pct, '.1f') + '%')
print('  sim_rules.slippage_bps   = ' + format(cfg2.sim_rules.slippage_bps, '.1f') + 'bps')
print('  broker.initial_cash (改) = $' + format(cfg2.broker.initial_cash, ',.0f'))

# C-3: 热加载
print('\n[C-3] FileWatcher 在 1s 内检测 yaml 修改并触发回调')
with tempfile.NamedTemporaryFile('w', suffix='.yaml', delete=False, encoding='utf-8') as f:
    f.write('broker:\n  type: simulation\n  initial_cash: 100\n')
    p = f.name
fired = threading.Event()
hits = [0]
def on_change(path):
    hits[0] += 1
    new = load_config(path)
    print('  callback fired #' + str(hits[0]) + ' cash=$' + format(new.broker.initial_cash, ',.0f'))
    if new.broker.initial_cash == 200:
        fired.set()

watcher = FileWatcher(p, on_change, interval=0.2)
watcher.start()
time.sleep(0.3)

with open(p, 'w', encoding='utf-8') as f:
    f.write('broker:\n  type: simulation\n  initial_cash: 200\n')
assert fired.wait(timeout=4), 'watcher 未触发'
watcher.stop()
os.unlink(p)
print('  热加载触发 OK')

# 清掉环境变量
os.environ.pop('NDX_RISK__STOP_LOSS_PCT', None)
os.environ.pop('NDX_SIM_RULES__SLIPPAGE_BPS', None)
os.environ.pop('NDX_BROKER__INITIAL_CASH', None)
