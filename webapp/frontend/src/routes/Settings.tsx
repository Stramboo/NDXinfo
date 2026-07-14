import { useEffect, useState } from "react";
import { api, type PriceAlert } from "../lib/api";
import { useTradeStore } from "../store/tradeStore";
import { usePreferenceStore } from "../store/preferenceStore";
import { Sun, Moon, RefreshCw, Bell, BellOff, Trash2, Eye, EyeOff } from "lucide-react";

export function Settings() {
  const prefs = usePreferenceStore();

  return (
    <div className="space-y-4 max-w-5xl pb-8">
      {/* 外观 */}
      <Section title="外观" hint="主题和默认交易标的。">
        <div className="space-y-4">
          <Theme />
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 block">
                默认交易标的
              </label>
              <input
                value={prefs.defaultSymbol}
                onChange={e => prefs.setDefaultSymbol(e.target.value.toUpperCase())}
                className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-fg tabular focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 block">
                默认K线周期
              </label>
              <select
                value={prefs.chartInterval}
                onChange={e => prefs.setChartInterval(e.target.value as any)}
                className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-fg focus:outline-none focus:border-emerald-500"
              >
                <option value="1d">日线</option>
                <option value="1h">1小时</option>
                <option value="15m">15分钟</option>
                <option value="5m">5分钟</option>
              </select>
            </div>
          </div>
        </div>
      </Section>

      {/* 通知 */}
      <Section title="通知" hint="价格告警触发时浏览器弹窗。">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {prefs.notificationsEnabled ? (
              <Bell className="h-5 w-5 text-emerald-400" />
            ) : (
              <BellOff className="h-5 w-5 text-fg-muted" />
            )}
            <div>
              <div className="text-sm text-fg font-medium">浏览器通知</div>
              <div className="text-xs text-fg-muted">
                {prefs.notificationsEnabled ? "已开启" : "已关闭"}
              </div>
            </div>
          </div>
          <button
            onClick={() => prefs.setNotificationsEnabled(!prefs.notificationsEnabled)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
              prefs.notificationsEnabled
                ? "bg-emerald-500 text-bg"
                : "bg-bg-subtle text-fg-muted hover:bg-bg-hover"
            }`}
          >
            {prefs.notificationsEnabled ? "关闭" : "开启"}
          </button>
        </div>
      </Section>

      {/* 告警管理 */}
      <Section title="价格告警" hint="管理已创建的价格告警。">
        <AlertManager />
      </Section>

      {/* 仪表盘布局 */}
      <Section title="仪表盘布局" hint="控制总览页面的面板显示/隐藏。">
        <LayoutCustomizer />
      </Section>

      {/* 仿真 */}
      <Section title="仿真模拟规则" hint="这些规则只对 Mock 引擎生效。">
        <SimRules />
      </Section>

      {/* 连接 */}
      <Section title="连接" hint="与后端 WebSocket 实时数据通道。">
        <ConnStatus />
      </Section>
    </div>
  );
}

function Section({ title, hint, children }: {
  title: string; hint?: string; children: React.ReactNode;
}) {
  return (
    <section className="panel-card p-5">
      <h2 className="text-fg text-lg font-semibold">{title}</h2>
      {hint && <p className="text-fg-muted text-sm mt-1">{hint}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}

function SimRules() {
  const [s] = useState({ slippage_bps: 0, commission_per_share: 0, t_plus_one: false });
  return (
    <div className="grid grid-cols-3 gap-3 text-xs text-fg-muted">
      <div className="bg-bg-subtle rounded-lg p-3">
        <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">滑点</div>
        <div className="text-fg">{s.slippage_bps} bps</div>
      </div>
      <div className="bg-bg-subtle rounded-lg p-3">
        <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">佣金</div>
        <div className="text-fg">${s.commission_per_share}/股</div>
      </div>
      <div className="bg-bg-subtle rounded-lg p-3">
        <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">T+1</div>
        <div className="text-fg">{s.t_plus_one ? "启用" : "关闭"}</div>
      </div>
    </div>
  );
}

function Theme() {
  const { theme, setTheme } = usePreferenceStore();
  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
      root.classList.remove("light");
    } else {
      root.classList.add("light");
      root.classList.remove("dark");
    }
    localStorage.setItem("ndxinfo.theme", theme);
  }, [theme]);
  return (
    <div className="flex gap-3">
      <Tile active={theme === "dark"} onClick={() => setTheme("dark")}>
        <Moon className="h-5 w-5 mx-auto mb-2" />深色
      </Tile>
      <Tile active={theme === "light"} onClick={() => setTheme("light")}>
        <Sun className="h-5 w-5 mx-auto mb-2" />浅色
      </Tile>
    </div>
  );
}

function AlertManager() {
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  useEffect(() => { api.alerts().then(setAlerts).catch(() => {}); }, []);

  if (alerts.length === 0) {
    return <p className="text-fg-muted text-sm">暂无告警。在自选列表中点击铃铛图标创建。</p>;
  }

  return (
    <div className="space-y-2">
      {alerts.map(a => (
        <div key={a.id} className="flex items-center justify-between bg-bg-subtle rounded-lg px-3 py-2.5">
          <div className="flex items-center gap-3">
            <span className={`h-2 w-2 rounded-full ${a.triggered ? "bg-amber-500 animate-pulse" : (a.enabled ? "bg-emerald-500" : "bg-fg-dim")}`} />
            <span className="text-sm font-semibold text-fg tabular">{a.symbol}</span>
            <span className="text-xs text-fg-muted">
              {a.condition === "above" ? "突破" : "跌破"} ${a.target_value}
            </span>
            {a.triggered ? (
              <span className="text-xs px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400">已触发</span>
            ) : null}
          </div>
          <button
            onClick={async () => {
              await api.deleteAlert(a.id);
              setAlerts(alerts.filter(x => x.id !== a.id));
            }}
            className="p-1 rounded text-fg-muted hover:text-rose-400 hover:bg-bg-hover transition"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}

function LayoutCustomizer() {
  const { dashboardLayout, togglePanel } = usePreferenceStore();
  const panelLabels: Record<string, string> = {
    "ndx-status": "NDX 大盘状态",
    "account-cards": "账户概览卡片",
    "equity-curve": "净值曲线",
    "positions": "当前持仓",
    "live-quotes": "实时报价",
    "recent-orders": "最近订单",
    "recent-signals": "最近信号",
  };

  return (
    <div className="grid grid-cols-2 gap-2">
      {Object.entries(panelLabels).map(([key, label]) => {
        const hidden = dashboardLayout.hiddenPanels.includes(key as any);
        return (
          <button
            key={key}
            onClick={() => togglePanel(key as any)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition border ${
              !hidden
                ? "bg-bg-subtle border-line text-fg hover:bg-bg-hover"
                : "bg-bg-input border-line text-fg-muted/50"
            }`}
          >
            {hidden ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5 text-emerald-400" />}
            {label}
          </button>
        );
      })}
    </div>
  );
}

function ConnStatus() {
  const ws = useTradeStore((s) => s.wsStatus);
  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2">
        <span className={
          "h-2 w-2 rounded-full " +
          (ws === "open" ? "bg-emerald-500" : ws === "closed" ? "bg-rose-500" : "bg-amber-500")
        } />
        <span className="text-sm">{ws === "open" ? "已连接" : ws === "closed" ? "已断开 (自动重连)" : "连接中"}</span>
      </div>
      <button
        onClick={() => window.location.reload()}
        className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-fg-muted bg-bg-subtle hover:bg-bg-hover transition"
      >
        <RefreshCw className="h-3.5 w-3.5" /> 刷新
      </button>
    </div>
  );
}

function Tile({ active, onClick, children }: {
  active?: boolean; onClick: () => void; children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={
        "flex-1 py-4 rounded-lg border text-sm transition " +
        (active
          ? "bg-emerald-500/10 border-emerald-500 text-emerald-400"
          : "bg-bg-subtle border-line text-fg-muted hover:bg-bg-hover")
      }
    >
      {children}
    </button>
  );
}
