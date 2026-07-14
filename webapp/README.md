# Trader WebApp — React + FastAPI

> 前后端分离的美股交易前端。**不动现有 `trader.py`**（PyQt5 GUI），
> 二者共用 `trading/` 业务逻辑（先 mock 数据，不依赖真实行情 / 券商）。

## 启动

### Windows 一键启动

```powershell
cd e:\Projects\NDXinfo
.\webapp\scripts\dev.ps1
```

### macOS / Linux

```bash
cd /path/to/NDXinfo
bash webapp/scripts/dev.sh
```

启动后：

| 服务 | URL | 用途 |
|---|---|---|
| **前端** | http://127.0.0.1:5173 | React 页面（你要看的） |
| **后端** | http://127.0.0.1:8765 | FastAPI |
| Swagger | http://127.0.0.1:8765/docs | REST 调试 |
| WebSocket | ws://127.0.0.1:8765/ws | 实时推送 |

> Vite 代理 `/api` 与 `/ws` 到后端，前端代码只需写相对路径。

## 手动启动（开发时用）

后端（终端 1）：

```powershell
cd e:\Projects\NDXinfo
python -m uvicorn webapp.backend.server:app --port 8765 --reload
```

前端（终端 2）：

```powershell
cd e:\Projects\NDXinfo\webapp\frontend
npm install           # 第一次运行装依赖
npm run dev
```

## 验证

```powershell
# 截 5 个页面的 PNG（要 Playwright + Chromium）
cd e:\Projects\NDXinfo
python -m webapp.scripts.capture_pages
#  → webapp/screenshots/{dashboard,trading,strategy,logs,settings,dashboard_light}.png
```

| 页面 | 路径 | 内容 |
|---|---|---|
| 总览 Dashboard  | `/`           | 4 个大数字 + 净值曲线 + 持仓 + 实时报价 + 最近订单 / 信号 |
| 交易 Trading    | `/trading`    | K 线 + 下单面板（市价/限价）+ 最近订单 |
| 策略 Strategy   | `/strategy`   | 8 策略选择 + 权重条 + 5 风控参数 |
| 日志 Logs       | `/logs`       | WS 推送的实时结构化日志（带 level / context） |
| 设置 Settings   | `/settings`   | 仿真规则 + 主题 + 连接状态 |

## 设计语言（简约 / 大气）

- **主色**：`#10B981` Emerald（涨）/ `#F43F5E` Rose（跌） / `#0A0B0F` 主背景
- **字体**：`Inter` + `JetBrains Mono`（数字） + `Noto Sans SC`（中文）
- **节奏**：12px 圆角 / 24px 间距 / 单色 + 一种强调色
- **模式**：默认深色；浅色作为附加项
- **图标**：`lucide-react`（24px / stroke 1.5）

全部在 `webapp/frontend/tailwind.config.js` 里以 design tokens 形式管理。

## 后端

`webapp/backend/`

- `server.py` — FastAPI 入口；lifespan 启动 1 个 ticker 协程（每秒推进 mock 引擎）
- `adapters/mock_engine.py` — 假行情 + 假账户 + 假订单 + 假信号
- `adapters/event_bus.py` — 内部 async pub/sub，桥接到 WebSocket

**REST 端点**（详见 `/docs`）：

| Method | Path | 用途 |
|---|---|---|
| GET  | `/api/health`           | 健康检查 |
| GET  | `/api/account`          | 账户 |
| GET  | `/api/positions`        | 持仓 |
| GET  | `/api/orders?limit=50`  | 订单 |
| POST | `/api/orders`           | 下单 |
| GET  | `/api/market/symbols`   | 监控列表 |
| GET  | `/api/market/{symbol}`  | 报价 |
| GET  | `/api/market/{symbol}/ohlc?limit=200` | K 线 |
| GET  | `/api/signals?limit=50` | 信号 |
| GET  | `/api/equity-history`   | 净值历史 |
| GET  | `/api/strategy`         | 当前策略 |
| GET  | `/api/limits`           | 风控 |
| WS   | `/ws`                   | 实时事件 |

**WS 事件**：

```ts
{ type: "tick",          data: { symbol, price, ts } }
{ type: "order_update",  data: Order }
{ type: "equity_update", data: { equity, cash, ... } }
{ type: "signal",        data: { symbol, action, strength, reason } }
{ type: "log",           data: { level, msg, ts, context } }
```

## 前端

`webapp/frontend/src/`

```
routes/        # 5 个页面
  Dashboard.tsx     总览
  Trading.tsx       交易
  Strategy.tsx      策略
  Logs.tsx          日志
  Settings.tsx      设置
components/    # 通用组件
  Sidebar.tsx       左侧栏 + WS 状态
  Header.tsx        顶部统计数字
features/      # 业务组件
  EquityCurve.tsx       净值曲线（纯 SVG，平滑曲线 + 渐变面积）
  KLineChart.tsx        TradingView Lightweight Charts
  OrderPanel.tsx        下单面板
  OrderHistory.tsx      订单历史
  PositionsTable.tsx    持仓表
  LiveSymbolsGrid.tsx   实时报价
lib/           # 客户端
  api.ts               fetch 客户端（带类型）
  ws.ts                WebSocket 客户端（自动重连 + 心跳）
  useBootstrapData.ts  启动拉一次初始数据
  utils.ts             cn / fmtMoney / fmtPct
store/
  tradeStore.ts        Zustand 中心 store（接 WS 事件）
styles/
  globals.css          Tailwind 入口 + 自定义 util
```

## 依赖

**后端 Python**（pip install 即可）：
- `fastapi`
- `uvicorn[standard]`
- `websockets`

**前端 Node**（npm install 自动装）：
- `react 18.3`
- `vite 5.4`
- `typescript 5.6`
- `tailwindcss 3.4`
- `lightweight-charts 4.2`
- `zustand 5.0`
- `react-router-dom 6.27`
- `lucide-react 0.454`

## 截图证据

`webapp/screenshots/`（`capture_pages.py` 产出，1440×900）：

| 文件 | 内容 |
|---|---|
| `dashboard.png`       | 深色总览（含净值曲线 + 持仓 + 实时报价） |
| `trading.png`         | 交易页（K 线 + 下单面板 + 订单历史） |
| `strategy.png`        | 策略页（8 策略选择 + 风控参数） |
| `logs.png`            | 实时日志（WS 推送） |
| `settings.png`        | 设置页（仿真规则 + 主题） |
| `dashboard_light.png` | 浅色主题 dashboard |

## 从 mock 切到真 trader

设环境变量 `NDXINFO_BACKEND=real`：

```powershell
# 用现有模拟券商（最稳）
$env:NDXINFO_BACKEND='real'
$env:NDXINFO_BROKER='simulation'
$env:NDXINFO_STRATEGY='multi'
$env:NDXINFO_CASH='100000'
python -m uvicorn webapp.backend.server:app --port 8765
```

## 接 Alpaca 实盘（Paper）

1. 注册 Alpaca Paper 账户：https://app.alpaca.markets/signup
2. 取 API Key：https://app.alpaca.markets/paper/dashboard/overview
3. 装 `alpaca-py`：

```powershell
pip install alpaca-py
```

4. 一键启动（脚本里有详细提示）：

```powershell
$env:APCA_API_KEY_ID='PK...'
$env:APCA_API_SECRET_KEY='SK...'
.\webapp\scripts\start_alpaca_paper.ps1
```

或者手工：

```powershell
$env:NDXINFO_BACKEND='real'
$env:NDXINFO_BROKER='alpaca'
$env:APCA_API_KEY_ID='PK...'
$env:APCA_API_SECRET_KEY='SK...'
python -m uvicorn webapp.backend.server:app --port 8765
```

切换完成后 Swagger 顶部的 health 端点会显示 `"backend": "real"`，
`api/positions` 直接是 Alpaca 的真实持仓。

## 已知 TODO

- 浅色主题首次启动会闪一下（Vite HMR）；刷新后正常
- K 线图首次加载偶发"❗"占位（lightweight-charts 加载延迟）
- WebSocket 偶尔 1.5s 间隔重连（Vite HMR proxy 抖动）

## 怎么停了

```powershell
Get-NetTCPConnection -State Listen -LocalPort 5173,8765 -EA SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -EA SilentlyContinue }
```
