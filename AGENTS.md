# AGENTS.md — AI Coding Agent 开发规则

> 给未来所有参与该项目的 AI Coding Agent 阅读的强制开发规则。

---

## 项目定位

TradeCamp 是一个**双子系统**组合项目：

| 子系统 | 定位 | 入口 |
|--------|------|------|
| 🅰️ 美股自动交易系统 | 生产级交易引擎 + PyQt5/React 双前端 | `trader.py`, `webapp/`, `trading/` |
| 🅱️ NASDAQ 每日分析报告 | 定时自动生成的技术分析 HTML 报告 | `nasdaq_analyzer.py` |

详细架构见 [ARCHITECTURE.md](ARCHITECTURE.md)。

---

## 技术栈

- **Python 3.10+**（核心语言，两个子系统共用）
- **TypeScript**（仅 WebApp 前端，`webapp/frontend/src/`）
- **pandas + numpy**（数据处理和指标计算，纯 Python，零 C 依赖）
- **PyQt5 + pyqtgraph**（桌面 GUI）
- **React 18 + Vite 5 + Tailwind CSS 3**（Web 前端）
- **FastAPI + WebSocket**（Web 后端）
- **SQLite**（两个独立的数据库）
- **Jinja2 + ECharts 5**（报告模板）
- **yfinance / Yahoo Direct API**（美股数据）
- **GitHub Actions**（CI + 定时报告）

---

## 开发原则

### 必须遵守

1. **最小范围修改**：每次只改完成当前任务必需的文件，不要顺手改无关代码
2. **理解已有设计意图**：修改前必须阅读相关模块的全部代码和文档
3. **不要随意重构**：现有架构经过多轮迭代形成，每个设计决策都有原因（参考 [DECISIONS.md](DECISIONS.md)）
4. **不要改变已有数据结构**：dict / DataFrame / dataclass 的输出格式是模板和下游模块的契约
5. **保持向后兼容**：`nasdaq_analyzer.py` 的输出格式（`REPORT_OUTPUT:path`）是 SOLO Schedule 的接口
6. **新增功能用 Feature Flags 包围**：所有可选功能必须通过 `ENABLE_*` 开关控制
7. **Graceful Degradation**：每个扩展模块必须独立 try/except，单个模块失败不阻断主流程

### 不允许的操作

- ❌ 删除或重命名 `REPORT_OUTPUT:` 输出格式
- ❌ 修改 `indicators.py` 中 `calc_all_indicators()` 的返回 DataFrame 列名
- ❌ 删除 Feature Flags 相关代码
- ❌ 在报告子系统中引入 PyQt5 依赖
- ❌ 在 `nasdaq_analyzer.py` 的主流程中添加需要 GUI 的代码
- ❌ 修改 `.github/workflows/daily-report.yml` 的时间配置（`0 21 * * 1-5`）除非理解其含义
- ❌ 删除 `echarts.min.js` 或改变它的文件名
- ❌ 混用两个 `backtest` 模块（根目录的 `backtest.py` 和 `backtest/engine.py` 是独立的）
- ❌ 修改 HTML 报告模板中 `chart_data` 的 JSON 键名（前端 JS 依赖这些键）
- ❌ 在未理解 Feature Flags 机制的情况下添加新的全局开关

---

## 修改代码前必须检查

### 通用检查

1. **阅读相关模块的全部代码**（用 Read 工具从头到尾读）
2. **搜索引用**：用 Grep 查找要修改的函数/类/常量在哪里被调用
3. **确认影响的子系统**：是 🅰️ 还是 🅱️？修改前确认不会跨界影响
4. **检查 [ROADMAP.md](ROADMAP.md)**：确定任务是否在 Not Doing 列表中
5. **检查 Feature Flags**：新功能是否需要通过 `ENABLE_*` 控制？

### 报告子系统（🅱️）特别检查

- 新指标在 `indicators.py` 中的列名是否与 `report_generator.py` 中 `_prepare_chart_data()` 的列名一致？
- 新图表数据是否通过 `chart_data` JSON 注入到模板？
- 模板中是否添加了对应的 ECharts JS 渲染代码？
- 新模块是否在 `nasdaq_analyzer.py` 的主流程中用 try/except 包裹？
- 是否需要更新 Feature Flags？

### 交易子系统（🅰️）特别检查

- 新策略是否继承 `StrategyBase` 并实现 `generate_signal()`？
- 是否需要更新 `trading/strategy.py` 中的 `create_strategy()` 工厂函数？
- 新券商是否需要实现 `trading/broker.py` 中的 Broker 接口？
- Web 前端改动是否需要在 `App.tsx` 中添加路由？

---

## 文件修改规范

### 修改 Python 文件

- 保持文件头部的 docstring 和作者注释不变
- 保持现有的 import 风格（分组：标准库 / 第三方 / 项目内部）
- 保持日志风格：`logger = logging.getLogger(__name__)`
- 所有新增函数/类必须有中文 docstring
- 不要在报告系统模块中引入 GUI 相关 import

### 修改 TypeScript/TSX 文件

- 保持 Tailwind CSS class 的命名规范
- 保持 design tokens 在 `tailwind.config.js` 中统一管理
- 新组件放在 `features/` 目录，新页面放在 `routes/` 目录

### 修改配置文件

- `config.py`：新常量必须带注释说明用途
- `config/default.yaml`：新字段必须带注释，保持嵌套结构
- 环境变量控制的新开关必须在 [ARCHITECTURE.md](ARCHITECTURE.md) 的 Feature Flags 部分记录

---

## 代码风格要求

### Python

```python
# 正确：中文 docstring
def calc_new_indicator(df, period=14):
    """计算新指标 - 使用 Wilder 平滑法"""
    ...

# 正确：Feature Flag 模式
if ENABLE_NEW_MODULE:
    try:
        from new_module import new_analysis
        result = new_analysis(data)
    except Exception as e:
        logger.warning(f"新模块分析失败: {e}")

# 正确：Graceful Degradation
if df is None or df.empty:
    logger.warning("数据不足，跳过")
    return None
```

### TypeScript

```tsx
// 正确：Tailwind 风格
<div className="flex items-center gap-2 p-4 bg-card rounded-lg">

// 正确：Zustand store 使用
const { equity, positions } = useTradeStore();
```

---

## 架构约束

### 不可跨越的边界

| 边界 | 规则 |
|------|------|
| 报告系统 ↔ 交易系统 | 只能通过 `NdxAdapter`（HTTP API）联动，不直接在代码中相互 import |
| 桌面端 ↔ Web 端 | 共用 `trading/` 业务逻辑，但 UI 代码完全独立 |
| `backtest.py` ↔ `backtest/` | 两个回测引擎互不引用，各自独立 |
| `config.py` ↔ `config/default.yaml` | 两个配置互不引用，服务于不同子系统 |
| CI ↔ 本地 | CI 特定的 Provider（`YahooDirectProvider`）不在本地强制使用 |

### 数据流约束

- 报告生成：`providers → data_fetcher → nasdaq_analyzer → report_generator → HTML`
- 交易引擎：`market_data → trading_engine → broker/strategy/risk → executor → GUI/WebApp`
- 联动：`NdxAdapter → HTTP /api/market/ndx → NdxStatusBar`

---

## 测试要求

### 运行已有验证流程

修改完代码后必须运行以下验证之一（根据修改范围）：

**修改了报告系统（🅱️）：**
```powershell
cd e:\Projects\TradeCamp
python nasdaq_analyzer.py
# 确认：10 个步骤全部成功，生成 HTML 报告
# 确认：控制台输出 REPORT_OUTPUT: 路径
```

**修改了交易系统（🅰️）：**
```powershell
cd e:\Projects\TradeCamp
pytest tests/
# 确认：7 个测试文件全部通过
```

**修改了 WebApp：**
```powershell
cd e:\Projects\TradeCamp
.\webapp\scripts\dev.ps1
# 确认：前端 http://127.0.0.1:5173 正常显示
# 确认：后端 http://127.0.0.1:8765/docs 可访问
```

**修改了 CI 相关文件：**
- 检查 `.github/workflows/smoke.yml` 中的依赖是否匹配 `requirements.txt`
- 检查 `.github/workflows/daily-report.yml` 中的依赖是否匹配 `requirements-report.txt`

---

## 完成任务后的汇报格式

每次完成任务后，向用户汇报以下内容：

```markdown
## 修改摘要
- 修改了哪些文件
- 每个文件的改动原因

## 验证结果
- 运行的验证命令和结果
- 确认没有破坏现有功能

## 注意事项（如有）
- 是否需要用户做额外操作
- 是否有需要确认的设计决策
```

---

## 参考文档

| 文档 | 用途 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统架构、目录结构、数据流 |
| [DECISIONS.md](DECISIONS.md) | 技术决策记录，理解每个选择的原因 |
| [ROADMAP.md](ROADMAP.md) | 当前状态、下一步计划、不做的事情 |
| [CHANGELOG.md](CHANGELOG.md) | 版本历史 |
| [README.md](README.md) | 项目总览和运行方式 |
| `.trae/documents/` | 原始设计文档和优化方案 |
