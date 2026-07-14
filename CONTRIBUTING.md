# 贡献指南

感谢你对 TradeCamp 的关注！我们欢迎各种形式的贡献。

---

## 目录

- [行为准则](#行为准则)
- [我可以贡献什么？](#我可以贡献什么)
- [开发环境搭建](#开发环境搭建)
- [提 Issue](#提-issue)
- [提 Pull Request](#提-pull-request)
- [代码规范](#代码规范)
- [项目结构速览](#项目结构速览)

---

## 行为准则

本项目采用 [Contributor Covenant 行为准则](CODE_OF_CONDUCT.md)。参与即表示你同意遵守。

---

## 我可以贡献什么？

### 🆕 新手友好

| 难度 | 贡献方向 |
|------|---------|
| ⭐ 入门 | 修正文档错别字、补全中文翻译、改进课程文案 |
| ⭐⭐ 基础 | 新增股市术语到术语词典、补充学习笔记 |
| ⭐⭐⭐ 中等 | 新增技术指标、优化回测策略参数 |
| ⭐⭐⭐⭐ 进阶 | 新增券商适配器、改进 AI 教练规则、开发新策略 |
| ⭐⭐⭐⭐⭐ 高级 | 统一回测引擎、架构重构、性能优化 |

### 💡 我们也需要

- **学习内容贡献者**：写课程、翻译、制作示意图
- **设计师**：改进 Web 界面、设计 Logo/品牌
- **文档**：完善教程、录制视频、写博客
- **测试**：提交 Bug 报告、编写测试用例
- **社区**：回答问题、帮助新人

---

## 开发环境搭建

### 前置条件

- Python 3.10+
- Node.js 18+（仅 Web 前端需要）
- Git

### 一键配置

```powershell
# 克隆仓库
git clone https://github.com/<your-org>/TradeCamp.git
cd TradeCamp

# Python 依赖
pip install -r requirements.txt

# Web 前端依赖（可选，仅改前端时需要）
cd webapp/frontend
npm install
cd ../..
```

### 验证环境

```powershell
# 验证报告系统（10 步流程全部成功即为正常）
python nasdaq_analyzer.py

# 验证交易系统（7 个测试文件全部通过）
pytest tests/

# 验证 Web 版（可选）
.\webapp\scripts\dev.ps1
# → http://127.0.0.1:5173
```

---

## 提 Issue

### Bug 报告

使用 Bug Report 模板，包含：
1. **环境信息**：操作系统、Python 版本、相关依赖版本
2. **复现步骤**：从零开始的具体操作
3. **期望行为 vs 实际行为**
4. **截图/日志**（如有）

### 功能建议

使用 Feature Request 模板，说明：
- 解决什么问题
- 对新手有什么帮助
- 可能的实现思路（可选）

### 学习相关问题

学习过程中的疑问也可以提 Issue，标签选 `question`。

---

## 提 Pull Request

### 流程

1. **Fork 本仓库**
2. **创建分支**：`git checkout -b feature/你的功能` 或 `fix/你的修复`
3. **写代码**：参考下方[代码规范](#代码规范)
4. **自测**：
   - 报告系统：`python nasdaq_analyzer.py`
   - 交易系统：`pytest tests/`
   - Web 前端：确保 `npm run dev` 正常
5. **提交**：使用 [约定式提交](https://www.conventionalcommits.org/zh-hans/) 格式
   ```
   feat(learning): 新增第 5 章技术分析课程
   fix(indicators): 修复 RSI 计算除零错误
   docs(readme): 更新快速开始指南
   ```
6. **发起 PR**：填写 PR 模板，关联相关 Issue

### PR 规范

- **一个 PR 只做一件事**：功能/修复/文档分开提交
- **保持向后兼容**：不破坏现有 API 和数据结构
- **新增功能用 Feature Flags 包裹**：参考 `config.py` 中的 `ENABLE_*` 模式
- **单模块失败不阻断主流程**：每个扩展模块用 try/except 包裹
- **通过 CI**：确保 GitHub Actions 检查全部通过

---

## 代码规范

### Python

```python
# ✅ 正确：中文 docstring + Feature Flag + Graceful Degradation
def calc_new_indicator(df, period=14):
    """计算新指标 - 使用 Wilder 平滑法"""
    ...

if ENABLE_NEW_MODULE:
    try:
        from new_module import new_analysis
        result = new_analysis(data)
    except Exception as e:
        logger.warning(f"新模块失败: {e}")
```

- 使用中文 docstring
- 新功能通过 `ENABLE_*` Feature Flag 控制
- 扩展模块独立 try/except，单模块失败不阻断主流程
- 日志用 `logging.getLogger(__name__)`
- 不修改 `indicators.py` 中 `calc_all_indicators()` 的返回列名
- 不在报告系统中引入 PyQt5 依赖

### TypeScript

- 保持 Tailwind CSS class 命名规范
- 新组件放 `webapp/frontend/src/features/`，新页面放 `routes/`
- Design tokens 在 `tailwind.config.js` 中统一管理

### 提交信息

```
<type>(<scope>): <描述>

type: feat | fix | docs | style | refactor | test | chore
scope: 可选，如 learning, indicators, webapp, backtest
描述: 中文，简洁明了
```

---

## 项目结构速览

```
TradeCamp/
├── 🅱️ 报告系统（nasdaq_analyzer.py 入口）
│   ├── indicators.py          # 10 大技术指标
│   ├── report_generator.py    # HTML 报告生成
│   ├── sentiment.py           # 情绪分析
│   └── ...
│
├── 🅰️ 交易系统（trader.py 入口）
│   ├── trading/               # 引擎/券商/策略/风控
│   ├── backtest/              # 回测引擎
│   ├── gui/                   # PyQt5 桌面版
│   ├── webapp/                # React + FastAPI Web 版
│   └── tests/                 # 单元测试
│
├── ARCHITECTURE.md            # 系统架构
├── DECISIONS.md               # 技术决策记录
├── ROADMAP.md                 # 路线图
└── AGENTS.md                  # AI 开发规则（AI 贡献者必读）
```

> 如果你是 AI 辅助开发，务必先阅读 [AGENTS.md](AGENTS.md)。

---

## 在哪里讨论？

- **GitHub Issues**：Bug、功能建议、问题求助
- **GitHub Discussions**：学习交流、经验分享、一般讨论（即将开放）

---

再次感谢你的贡献！每一个 PR、每一个 Issue、甚至每一处错别字修正，都在帮助更多新手走上投资学习之路。
