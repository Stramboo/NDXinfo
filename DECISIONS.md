# TradeCamp 技术决策记录

记录项目中重要的技术和产品决策。格式：编号 - 决策名称。

---

## D001 - 纯 pandas 实现技术指标

**Date:** 2026-07-13

**Background:**
需要计算 MA/MACD/RSI/KDJ/BOLL 等常见技术指标。常见的 Python 量化库如 TA-Lib 需要 C 编译，在 Windows 上安装困难；`pandas-ta` 功能强大但引入额外依赖。

**Decision:**
选用纯 pandas + numpy 实现所有 10 个技术指标。指标计算内联在 `indicators.py` 中，使用 `calc_all_indicators(df)` 统一入口。

**Reason:**
- 零外部依赖，Windows/macOS/Linux/GitHub Actions 均可直接运行
- pandas 是已引入的核心依赖
- 10 个指标均在 ~200 行代码内完成，维护成本可接受
- 对于每日分析场景，不需要 TA-Lib 级别的性能优化

**Rejected Alternatives:**
- TA-Lib：需要 C 编译，Windows 环境体验差，GitHub Actions 需额外安装步骤
- pandas-ta：额外依赖，功能远超当前需求

**Impact:**
所有指标计算在本地完成，无外部库依赖风险。

---

## D002 - ECharts 本地优先 + CDN 回退

**Date:** 2026-07-13

**Background:**
HTML 报告需要图表渲染。ECharts 5 官方 CDN（jsdelivr）在中国大陆偶尔不可用，且 GitHub Actions CI 环境可能无法访问 CDN。

**Decision:**
将 `echarts.min.js`（~1MB）下载到项目根目录，HTML 模板优先加载本地文件，CDN 作为回退。`report_generator.py` 在生成报告时自动将 `echarts.min.js` 复制到报告输出目录。

**Reason:**
- 本地文件确保离线环境和网络受限环境下图表正常渲染
- CDN 回退机制增加容错
- ~1MB 文件体积对 Git 仓库和 GitHub Actions 均可接受

**Impact:**
项目根目录需包含 `echarts.min.js` 文件。

---

## D003 - Feature Flags 控制可选模块

**Date:** 2026-07-13

**Background:**
报告系统扩展了多个可选模块（回测、情绪分析、板块轮动、ML 预测等），不同环境（本地/CI/Docker）可能需要不同的功能组合。部分模块有重型依赖（Prophet/scikit-learn），不应强制安装。

**Decision:**
在 `config.py` 中定义 `ENABLE_*` Feature Flags，通过环境变量覆盖。主流程 `nasdaq_analyzer.py` 中所有添加功能用 `if ENABLE_XXX:` 包裹，单个模块失败用 try/except 捕获后记录日志并继续。

**Reason:**
- 核心报告流程不受影响，新增模块可独立启停
- 降低依赖复杂度（不装 ML 依赖也能正常生成报告）
- Docker 镜像、GitHub Actions 可按需开关

**Impact:**
所有新增功能模块必须遵循 Feature Flags + Graceful Degradation 模式。

---

## D004 - SQLite 选择（非 MySQL/PostgreSQL）

**Date:** 2026-07-13

**Background:**
需要持久化每日价格快照、指标快照、报告元数据，以支持历史对比和指标历史查询。

**Decision:**
使用 Python 标准库 `sqlite3`，数据库文件放在 `data/nasdaq.db`。

**Reason:**
- Python 标准库自带，零安装零配置
- 文件型数据库，个人单用户场景够用
- 不需要独立数据库服务进程
- 与 Docker 容器部署天然兼容（单文件挂载即可）

**Rejected Alternatives:**
- MySQL/PostgreSQL：需要额外的数据库服务，对个人工具是过度工程
- DuckDB：虽然性能更好但额外依赖，SQLite 已满足需求

**Impact:**
所有数据存储在本地 SQLite 文件中。

---

## D005 - 两个 backtest 模块并存

**Date:** 2026-07-14

**Background:**
v1.1 在根目录创建了 `backtest.py`（嵌入式回测，直接操作 pandas DataFrame 的简易引擎）。v2.0 的 `trading/` 子系统需要更专业的回测，因此在 `backtest/` 目录下创建了新引擎（基于 StrategyBase + RiskManager + Portfolio 的专业引擎）。

**Decision:**
保持两个模块并存，用不同的命名空间区分：
- `backtest.py`（根目录）：报告器内轻量回测，MACD+RSI+WR 固定策略
- `backtest/engine.py`：独立回测引擎，可与任何交易策略搭配使用

**Reason:**
- 报告系统的回测与交易系统的回测需求不同（报告侧重展示，交易侧重精度）
- 两个模块不互相依赖，风险隔离
- 未来 P0 计划统一，但当前阶段不急于迁移

**Impact:**
- 存在代码重复和两个回测结果不一致的风险
- ROADMAP P0 已计划统一

---

## D006 - PyQt5 + React 双前端

**Date:** 2026-07-14

**Background:**
交易系统需要用户界面。PyQt5 提供原生 Windows 桌面体验（高性能 K 线图、系统托盘），React + FastAPI 则适合跨平台浏览器访问。

**Decision:**
同时支持 PyQt5 桌面 GUI 和 React WebApp 两种前端，共用 `trading/` 业务逻辑。

**Reason:**
- PyQt5 桌面端提供更好的性能（本地渲染 K 线图）和系统集成（托盘通知）
- React Web 端提供跨平台能力和远程访问
- 两种方式各有场景，不互斥

**Impact:**
- 需要维护两套前端代码
- Web 端通过适配器层（`engine_adapter.py`）桥接真实的 `TradingEngine`

---

## D007 - Yahoo Direct API 绕道方案

**Date:** 2026-07-14

**Background:**
yfinance 在 GitHub Actions CI 环境频繁失败（IP 限制 / Cloudflare 挑战 / 返回空数据）。需要更可靠的 CI 数据获取方案。

**Decision:**
新增 `YahooDirectProvider`，直接调用 `query1.finance.yahoo.com/v8/finance/chart` JSON API，彻底绕过 yfinance 库。同时引入 `USE_ETF_PROXY` 开关用 QQQ/VIXY 替代 ^IXIC/^VIX。

**Reason:**
- Direct API 不需要经过 yfinance 的网络层，成功率显著提高
- ETF 代理（QQQ）走势与纳指几乎一致，数据质量可接受
- 两个方案都是环境变量控制的可选开关，不影响本地使用

**Impact:**
- CI 环境需要使用 `USE_DIRECT_API=true` + `USE_ETF_PROXY=true`
- Direct API 返回数据格式需转换为与 yfinance 一致（已在 `yahoo_direct_provider.py` 中处理）

---

## D008 - WebApp 默认 mock 模式

**Date:** 2026-07-14

**Background:**
WebApp 需要展示功能齐全的界面。真引擎依赖外部行情数据，启动慢、不稳定。

**Decision:**
WebApp 默认使用 MockEngine（模拟行情 + 模拟账户），通过环境变量 `NDXINFO_BACKEND=real` 切换到真正的 TradingEngine。

**Reason:**
- Mock 模式确保页面始终可演示，不受网络/API 状态影响
- 开发时不需要等待真实行情加载，热更新体验好
- 真实的交易引擎作为可选切换

**Impact:**
WebApp 后端需要适配器层同时支持 MockEngine 和 EngineAdapter。

---

## D009 - 中英文金融词典情绪分析

**Date:** 2026-07-13

**Background:**
需要评估市场新闻的情绪倾向。传统的 NLP 方案（FinBERT）需要 GPU 推理，HuggingFace 模型体积大（>400MB），对个人工具不友好。

**Decision:**
使用词典法（lexicon-based），中英文金融情感词典在代码中硬编码。正面词 +1 分，负面词 -1 分，按词频归一化。

**Reason:**
- 零依赖，零模型下载
- 对财经新闻场景，词典法准确度足够
- 代码体积小（约 200 行）

**Rejected Alternatives:**
- FinBERT：需 transformers 库 + 模型下载，太重
- TextBlob/VADER：仅英文，不支持中文

**Impact:**
情绪精度有限但日常可用。支持中英文双语新闻。

---

## D010 - GitHub Actions gh-pages 发布

**Date:** 2026-07-14

**Background:**
每日生成的 HTML 报告需要能在浏览器中直接查看。直接放在仓库中无法通过 GitHub 直接打开 HTML 文件。

**Decision:**
使用 `peaceiris/actions-gh-pages` Action 将报告推送到 `gh-pages` 分支，通过 GitHub Pages 提供静态托管。使用 `keep_files: true` 保留历史报告。

**Reason:**
- 免费、零运维
- 历史报告自然归档
- 浏览器直接访问 URL

**Impact:**
报告可通过 `https://<user>.github.io/<repo>/nasdaq_report_YYYY-MM-DD.html` 访问。

---

## D011 - AI 教练规则驱动（可选 LLM）

**Date:** 2026-07-14

**Background:**
需要为交易者提供个性化建议和段位评估。纯 AI（LLM）方案成本高、延迟大。

**Decision:**
规则驱动作为主方案：段位计算、持仓体检、风险预警均基于硬编码规则 + 技术指标。预留 LLM 增强接口（`call_llm()` 函数）。

**Reason:**
- 离线可用，无 API 费用
- 规则可解释、可调试
- 延迟 < 10ms vs LLM 的 > 1s
- LLM 作为可选的增强层，不影响核心功能

**Impact:**
所有教练功能在没有 LLM 的环境中也能正常工作。

---

## D012 - 多因子 AI 推荐引擎

**Date:** 2026-07-14

**Background:**
需要为每只被监控的股票给出操作建议（BUY/HOLD/SELL），不能只是展示数据。

**Decision:**
5 因子加权评分模型：
- 趋势因子 30%（均线排列、价格位置）
- 动量因子 25%（MACD、KDJ 信号）
- 反转因子 20%（RSI、布林带超买超卖）
- 量价因子 15%（成交量变化、OBV 方向）
- 波动因子 10%（ATR、布林带宽度）

**Reason:**
- 每个因子基于已有技术指标，零额外数据需求
- 加权设计可调整，不需要训练数据
- 评分可解释（每个因子有独立得分和理由）

**Impact:**
推荐引擎与交易策略使用相同的技术指标输入，但评分逻辑独立。

---

## 不确定项

以下决策的原因或时间**需要项目所有者确认**：

1. **D005（两个 backtest 并存）**— P0 的统一计划是否已经开始？是否考虑过直接删除根目录的 `backtest.py`？
2. **D007（Yahoo Direct API）**— Yahoo 是否可能更改 `query1.finance.yahoo.com` 的 API 格式？
3. **数据库路径**— `data/userdata.db` 和 `data/nasdaq.db` 是否应该合并为一个数据库？
