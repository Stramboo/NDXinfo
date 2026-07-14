# Examples — trader 一键复现脚本

这组 demo 脚本对应 trader 优化方案中所有 P0/P1/P2 任务的端到端验收。
**它们都跑离线**，不依赖真实网络数据，可在一台普通开发机上重复运行。

## 一键运行

```cmd
cd e:\Projects\NDXinfo
examples\run_all_demos.bat
```

预计 1 ~ 3 分钟跑完（pytest 约 2s + 每个 demo 平均 5~10s）。

## 各 demo 的任务映射

| 文件 | 对应计划任务 | 验收 |
| --- | --- | --- |
| `demo_a_broker_basic.py`     | A — 模拟券商默认行为 | 向后兼容（无滑点/无佣金/无 T+1）下，价格字节级一致 |
| `demo_b_broker_rules.py`     | A — 滑点 / 佣金 / T+1 / 拒绝码 | 滑点公式校验；T+1 拦截；拒绝原因码 |
| `demo_c_backtest.py`         | E — 回测引擎 | Sharpe/MaxDD/Calmar/PF/WinRate 12 项指标 + 报告 |
| `demo_d_config.py`           | F — YAML / env / 热加载 | default + env override + FileWatcher |
| `demo_e_observability.py`    | G — JSON 日志 / SQLite | context 字段、4 张表、stats CLI |
| `demo_f_strategies.py`       | H — 新旧 8 策略对比 | 5 旧 + 3 新 + ensemble weighted reason |
| `demo_g_ui_theme.py`         | D — 浅色 / 深色 主题 | 调色板切换 + GUI widgets import |
| `capture_gui.py`             | D — TraderMainWindow 截图 | dark + light PNG，输出到 `screenshots/` |

## 单独跑某一个

```powershell
cd e:\Projects\NDXinfo
python examples\demo_a_broker_basic.py
python examples\demo_c_backtest.py
...
```

## 与 trader.py 主入口的关系

`demo_*.py` 与 `trader.py` 互不干扰：

- `trader.py` 是真实交易入口（GUI / CLI / auto）
- `examples\demo_*.py` 是单元级 + 集成级的快照式复现脚本

`python trader.py --no-gui --auto` 是真实运行的演示，
`run_all_demos.bat` 是纯逻辑层的演示。
