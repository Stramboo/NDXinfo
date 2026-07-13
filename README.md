# NASDAQ 每日分析报告程序

> 自动分析美国纳斯达克指数及重点个股，每日生成包含技术指标、趋势分析、个股推荐、策略回测、板块轮动、新闻情绪的交互式 HTML 报告。

## 功能特性

### 核心分析
- **指数行情分析**：NASDAQ 综合指数(^IXIC)、NASDAQ-100(^NDX)、VIX 恐慌指数
- **十大技术指标**：MA、MACD、RSI、KDJ、布林带、**ATR**（平均真实波幅）、**OBV**（能量潮）、**WR**（威廉指标）、**CCI**（商品通道指标）、**VWAP**（成交量加权均价）
- **趋势与信号判断**：均线排列趋势识别、支撑/阻力位、MACD金叉/死叉、RSI超买/超卖、KDJ信号、布林突破、WR超买超卖、CCI突破±100、VWAP偏离
- **个股推荐**：覆盖半导体/AI、大型科技、成长/创新三大板块，12只重点个股
- **动态涨幅榜**：每日自动筛选 NASDAQ 涨幅榜 Top 10

### 扩展模块（Feature Flags 开关控制）
- **策略回测分析**（`ENABLE_BACKTEST`）：MACD+RSI+WR 组合策略回测，净值曲线、夏普比率、最大回撤、胜率等指标
- **板块轮动分析**（`ENABLE_SECTOR_ETF`）：11个行业ETF + 4个宽基ETF相对强度分析，动量评分与排名
- **新闻情绪分析**（`ENABLE_NEWS_SENTIMENT`）：中英文金融词典情绪分析，AKShare + yfinance 双数据源
- **历史报告对比**（`ENABLE_COMPARISON`）：与上期报告对比趋势/VIX/市场宽度/价格/推荐变化
- **港股/A股支持**（`ENABLE_HK_A_SHARE`）：通过 AKShare 获取港股/A股数据
- **报告归档**：自动归档到 `reports/` 目录并写入 SQLite 数据库

### 报告体验
- **交互式 HTML 报告**：基于 ECharts 的 K线图、仪表盘、柱状图、折线图，暗色金融主题
- **可折叠指标面板**：ATR/OBV/WR/CCI/VWAP 等扩展指标使用 `<details>` 折叠展示
- **报告归档与对比**：历史报告存入 SQLite，支持与上期报告自动对比
- **定时自动运行**：支持 cron 定时任务，每日自动生成报告

## 报告预览

| 模块 | 内容 |
|------|------|
| 市场概览 | IXIC/NDX/VIX/市场宽度 四大指标卡片 |
| VIX/RSI 仪表盘 | 恐慌指数与超买超卖可视化 |
| K线技术分析 | candlestick + MA均线 + 布林带 + dataZoom |
| 成交量副图 | 红绿区分涨跌 |
| MACD 副图 | DIF/DEA 折线 + 红绿柱状 |
| 趋势分析 | 趋势方向 + 支撑/阻力位 + 关键信号 |
| 个股推荐表 | 代码/名称/现价/涨跌/RSI/趋势/信号/建议 |
| 动态涨幅榜 | NASDAQ 当日涨幅 Top 10 横向柱状图 |
| **历史对比** | 与上期报告的趋势/VIX/价格/推荐变化对比 |
| **策略回测** | 净值曲线 + 8项核心指标 + 交易记录 |
| **新闻情绪** | 情绪得分仪表 + 新闻列表（含情绪标签） |
| **板块轮动** | 11行业ETF横向柱状图 + 强弱排名表 |
| **扩展指标** | ATR/OBV/WR/CCI/VWAP 可折叠子图 |

## 快速开始

### 环境要求

- Python 3.9+
- 网络可访问 Yahoo Finance

### 安装

```bash
git clone https://github.com/Stramboo/NDXinfo.git
cd NDXinfo
pip install -r requirements.txt
```

### 运行

```bash
python nasdaq_analyzer.py
```

运行后在项目根目录生成 `nasdaq_report_YYYY-MM-DD.html`，用浏览器打开即可查看。

### 定时任务（可选）

使用 cron 设置每日自动运行（北京时间周二至周六凌晨5点，对应美股交易日收盘后）：

```cron
0 5 * * 2-6 cd /path/to/NDXinfo && python nasdaq_analyzer.py
```

## Feature Flags 配置

通过环境变量控制各功能模块的开关（默认值见 `config.py`）：

| 环境变量 | 默认 | 说明 |
|----------|------|------|
| `ENABLE_BACKTEST` | `true` | 策略回测分析 |
| `ENABLE_NEWS_SENTIMENT` | `true` | 新闻情绪分析 |
| `ENABLE_SECTOR_ETF` | `true` | 板块轮动分析 |
| `ENABLE_COMPARISON` | `true` | 历史报告对比 |
| `ENABLE_HK_A_SHARE` | `false` | 港股/A股数据 |
| `ENABLE_ML_PREDICT` | `false` | ML价格预测（实验性） |
| `ENABLE_PDF_EXPORT` | `false` | PDF导出（实验性） |
| `ENABLE_EMAIL` | `false` | 邮件推送（实验性） |

使用示例：

```bash
# 关闭回测和板块分析，加快运行速度
ENABLE_BACKTEST=false ENABLE_SECTOR_ETF=false python nasdaq_analyzer.py

# 开启港股/A股支持（需安装 akshare）
ENABLE_HK_A_SHARE=true pip install akshare && python nasdaq_analyzer.py
```

## 项目结构

```
NDXinfo/
├── nasdaq_analyzer.py          # 主入口脚本（10步流程 + Feature Flags）
├── config.py                   # 配置：股票池、路径、指标参数、Feature Flags
├── data_fetcher.py             # 数据获取 Facade（路由至各 Provider）
├── indicators.py               # 技术指标计算（10大指标，纯 pandas）
├── analysis.py                 # 趋势分析、信号判断、VIX情绪
├── backtest.py                 # 策略回测引擎（MACD+RSI+WR 组合策略）
├── sentiment.py                # 新闻情绪分析（中英文金融词典）
├── sector.py                   # 板块轮动分析（11行业ETF + 4宽基ETF）
├── db.py                       # SQLite 存储层（5表结构）
├── comparison.py               # 历史报告对比模块
├── report_generator.py         # HTML 报告生成（Jinja2 + ECharts + 归档）
├── providers/                  # 多数据源抽象层
│   ├── __init__.py             # 包初始化
│   ├── base.py                 # DataProvider 抽象基类
│   ├── yfinance_provider.py    # yfinance 数据源（美股）
│   └── akshare_provider.py     # akshare 数据源（港股/A股）
├── templates/
│   └── report_template.html    # Jinja2 模板（暗色金融主题）
├── echarts.min.js              # ECharts 5 本地库（离线渲染）
├── data/                       # SQLite 数据库存储目录
│   └── nasdaq.db               # 历史数据、报告、指标快照
├── reports/                    # 报告归档目录
├── requirements.txt            # Python 依赖
├── LICENSE
└── README.md
```

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 数据源 | yfinance + akshare | yfinance(美股) / akshare(港股/A股/新闻)，免费无需API Key |
| 数据架构 | Provider 抽象层 | Facade 模式，按 ticker 前缀路由至不同数据源 |
| 指标计算 | pandas + numpy | 纯 Python，无 TA-Lib 依赖 |
| 回测引擎 | 纯 pandas | 轻量级，无 backtrader/vectorbt 依赖 |
| 数据存储 | SQLite | 5表结构，幂等写入，历史对比 |
| 报告渲染 | Jinja2 | 模板引擎，逻辑与视图分离 |
| 图表可视化 | ECharts 5 | 交互式 K线/仪表盘/柱状图/折线图 |
| 主题 | CSS Variables | 暗色金融风格，涨绿跌红 |
| 功能开关 | Feature Flags | 环境变量控制，优雅降级 |

## 个股池

| 板块 | 股票 |
|------|------|
| 半导体/AI芯片 | NVDA, AMD, TSM, AVGO |
| 大型科技股 | AAPL, MSFT, GOOGL, AMZN, META |
| 成长/创新股 | TSLA, PLTR, COIN |

可在 `config.py` 中自定义股票池。如启用 `ENABLE_HK_A_SHARE`，还可配置 `HK_STOCK_UNIVERSE` 和 `A_SHARE_UNIVERSE`。

## 配置说明

编辑 `config.py` 可调整：

- `STOCK_UNIVERSE`：自定义关注的股票池
- `MA_PERIODS`：移动平均线周期（默认 5/10/20/60）
- `RSI_PERIOD`：RSI 周期（默认 14）
- `MACD_FAST/SLOW/SIGNAL`：MACD 参数（默认 12/26/9）
- `CHART_DISPLAY_DAYS`：图表显示天数（默认 60）
- `SCREENER_TOP_N`：涨幅榜数量（默认 10）
- `ATR_PERIOD` / `WR_PERIOD` / `CCI_PERIOD` / `VWAP_PERIOD`：新指标周期参数
- `BACKTEST_INITIAL_CAPITAL` / `BACKTEST_COMMISSION` / `BACKTEST_LOOKBACK`：回测参数
- `SECTOR_ETFS` / `BROAD_INDEX_ETFS`：板块ETF配置
- `HK_STOCK_UNIVERSE` / `A_SHARE_UNIVERSE`：港股/A股股票池

## 免责声明

本程序自动生成的报告仅供学习和参考使用，**不构成任何投资建议**。投资有风险，入市需谨慎。技术指标基于历史数据计算，不能保证未来走势。回测结果不代表未来收益。请在投资前咨询专业财务顾问。

## License

[MIT](LICENSE)
