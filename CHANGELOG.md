# Changelog

记录用户可感知的重要变化。

## Unreleased

### Added
- AI 教练系统：每日简报、持仓体检、段位评估、操作建议
- AI 推荐引擎：多因子评分模型，每只股票综合评分 + BUY/HOLD/SELL 建议
- 股市学习系统：8 章入门课程 + 50+ 术语词典 + 新手引导
- Web 版组合管理页面（Portfolio）
- Web 版交易日志页面（Journal）
- Web 版专用交易面板（TradingDesk）
- NDX 大盘分析页面（Analysis）：将 NASDAQ 报告数据整合到 Web 前端

### Changed
- README 重写：清晰描述两个子系统的关系和联动
- CI：为 Windows runner 设置 `PYTHONIOENCODING=utf-8` 防止中文编码报错

---

## Previous Versions

### v2.0 — 2026-07-14

#### Added
- **美股自动交易系统**（新子系统）：
  - 模拟券商 + Alpaca 实盘券商
  - 8 个交易策略（MACD / RSI / MA Trend / Bollinger / Multi / KDJ / Boll-width / Ensemble）
  - 风控模块（仓位上限 / 止损 / 移动止损 / ATR 止损）
  - 独立回测引擎（`backtest/`）与 12 项评估指标
  - PyQt5 桌面 GUI（深/浅主题，Dashboard / Trading / Strategy）
  - React 18 + FastAPI Web 版（前后端分离，WebSocket 实时推送）
  - 交易系统与报告系统轻联动（Dashboard 显示 NDX 状态）
- GitHub Actions CI（smoke workflow）：pytest + demos + GUI 截图 + 主题切换验证

### v1.1 — 2026-07-13

#### Added
- 5 个新增技术指标：ATR / OBV / WR / CCI / VWAP（总计 10 个）
- 轻量回测引擎（`backtest.py`）：MACD+RSI+WR 组合策略
- 新闻情绪分析（`sentiment.py`）：中英文金融词典法
- 板块轮动分析（`sector.py`）：11 大行业 ETF + 4 宽基指数
- 历史报告对比（`comparison.py`）：与上期报告的关键变化
- 多数据源 Provider 架构（`providers/`）：yfinance / YahooDirectAPI / AKShare
- SQLite 存储层（`db.py`）：价格 / 指标 / 报告 / 回测 / 预测持久化
- ML 价格预测模块（`ml_predictor.py`）：Prophet + sklearn 备选
- Docker 容器化（多阶段构建）
- GitHub Actions 每日定时报告工作流
- Feature Flags 机制（`ENABLE_*` 环境变量控制各功能开关）

#### Changed
- `data_fetcher.py` 重构为 Facade，路由多 Provider
- 报告模板支持可折叠副图和新指标展示

### v1.0 — 2026-07-13

#### Added
- NASDAQ 每日分析报告程序初版
- 5 个基础技术指标：MA(5/10/20/60) / MACD / RSI / KDJ / BOLL
- 趋势分析、支撑阻力位、交易信号生成
- VIX 情绪分析、市场宽度分析
- 12 只重点美股（3 个板块）推荐系统
- NASDAQ 涨幅榜动态筛选
- Jinja2 + ECharts 5 暗色主题 HTML 报告
- 10 步主流程（`nasdaq_analyzer.py`）
- SOLO 定时任务每日自动执行
