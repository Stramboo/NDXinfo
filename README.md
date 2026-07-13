# NASDAQ 每日分析报告程序

> 自动分析美国纳斯达克指数及重点个股，每日生成包含技术指标、趋势分析、个股推荐的交互式 HTML 报告。

## 功能特性

- **指数行情分析**：NASDAQ 综合指数(^IXIC)、NASDAQ-100(^NDX)、VIX 恐慌指数
- **五大技术指标**：MA 移动平均线、MACD、RSI、KDJ、布林带（纯 pandas 实现，零 C 依赖）
- **趋势与信号判断**：均线排列趋势识别、支撑/阻力位、MACD金叉/死叉、RSI超买/超卖、KDJ信号、布林突破
- **个股推荐**：覆盖半导体/AI、大型科技、成长/创新三大板块，12只重点个股
- **动态涨幅榜**：每日自动筛选 NASDAQ 涨幅榜 Top 10
- **交互式 HTML 报告**：基于 ECharts 的 K线图、仪表盘、柱状图，暗色金融主题
- **定时自动运行**：支持 cron 定时任务，每日自动生成报告

## 报告预览

报告包含以下模块：

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

## 快速开始

### 环境要求

- Python 3.9+
- 网络可访问 Yahoo Finance

### 安装

```bash
git clone https://github.com/你的用户名/NDXinfo.git
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

## 项目结构

```
NDXinfo/
├── nasdaq_analyzer.py          # 主入口脚本（10步流程）
├── config.py                   # 配置：股票池、路径、指标参数
├── data_fetcher.py             # yfinance 数据获取（限流、重试、异常处理）
├── indicators.py               # 技术指标计算（纯 pandas）
├── analysis.py                 # 趋势分析、信号判断、VIX情绪
├── report_generator.py         # HTML 报告生成（Jinja2 + ECharts）
├── templates/
│   └── report_template.html    # Jinja2 模板（暗色金融主题）
├── echarts.min.js              # ECharts 5 本地库（离线渲染）
├── requirements.txt            # Python 依赖
├── LICENSE
└── README.md
```

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 数据源 | yfinance | 免费，无需 API Key |
| 指标计算 | pandas + numpy | 纯 Python，无 TA-Lib 依赖 |
| 报告渲染 | Jinja2 | 模板引擎，逻辑与视图分离 |
| 图表可视化 | ECharts 5 | 交互式 K线/仪表盘/柱状图 |
| 主题 | CSS Variables | 暗色金融风格，涨绿跌红 |

## 个股池

| 板块 | 股票 |
|------|------|
| 半导体/AI芯片 | NVDA, AMD, TSM, AVGO |
| 大型科技股 | AAPL, MSFT, GOOGL, AMZN, META |
| 成长/创新股 | TSLA, PLTR, COIN |

可在 `config.py` 中自定义股票池。

## 配置说明

编辑 `config.py` 可调整：

- `STOCK_UNIVERSE`：自定义关注的股票池
- `MA_PERIODS`：移动平均线周期（默认 5/10/20/60）
- `RSI_PERIOD`：RSI 周期（默认 14）
- `MACD_FAST/SLOW/SIGNAL`：MACD 参数（默认 12/26/9）
- `CHART_DISPLAY_DAYS`：图表显示天数（默认 60）
- `SCREENER_TOP_N`：涨幅榜数量（默认 10）

## 免责声明

本程序自动生成的报告仅供学习和参考使用，**不构成任何投资建议**。投资有风险，入市需谨慎。技术指标基于历史数据计算，不能保证未来走势。请在投资前咨询专业财务顾问。

## License

[MIT](LICENSE)
