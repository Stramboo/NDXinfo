/**
 * TradingDesk — 自动操盘控制中心
 *
 * 功能：
 * - 启动/停止自动交易
 * - 实时查看策略信号流
 * - 监控账户/持仓/订单变化
 * - 设置扫描间隔和风控参数
 * - 一键手动干预（全平仓/暂停）
 */

import { useEffect, useState, useRef } from "react";
import {
  Play, Square, Activity, Zap, Shield, BarChart3, TrendingUp,
  Clock, DollarSign, AlertTriangle, Check, X, RefreshCw,
  Radio, Pause,
} from "lucide-react";
import { api } from "../lib/api";
import { useTradeStore } from "../store/tradeStore";
import { fmtMoney, fmtPct, relTime } from "../lib/utils";

type TradeStatus = {
  running: boolean;
  mode: string;
  strategy: string;
  tick_count: number;
  success: number;
  errors: number;
  interval_s: number;
  account?: any;
  positions_count?: number;
  last_error?: string;
  error?: string;
};

type TradeEvent = {
  type: string;
  action: string;
  strategy?: string;
  interval_s?: number;
  ts: number;
};

export function TradingDesk() {
  const [status, setStatus] = useState<TradeStatus | null>(null);
  const [interval, setInterval_s] = useState(60);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [events, setEvents] = useState<TradeEvent[]>([]);
  const [signals, setSignals] = useState<any[]>([]);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const tradeStore = useTradeStore();
  const account = tradeStore.account;
  const orders = tradeStore.orders;
  const wsStatus = tradeStore.wsStatus;

  // 轮询状态
  const fetchStatus = async () => {
    try {
      const s = await api.tradeStatus();
      setStatus(s);
    } catch { /* ignore */ }
  };

  useEffect(() => {
    fetchStatus();
    pollRef.current = setInterval(fetchStatus, 3000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  // 监听 WebSocket auto_trade 事件
  useEffect(() => {
    // 偷听 store 里的最新 orders 变化（通过轮询 orders 列表）
    const check = setInterval(() => {
      const s = useTradeStore.getState().signals;
      if (s.length > signals.length) {
        setSignals(s.slice(0, 20));
      }
    }, 2000);
    return () => clearInterval(check);
  }, [signals.length]);

  const doAction = async (action: "start" | "stop") => {
    setLoading(true);
    setMsg(null);
    try {
      await api.tradeControl(action, interval);
      setMsg({ ok: true, text: action === "start" ? "自动交易已启动！" : "自动交易已停止" });
      setEvents(prev => [{
        type: "control", action,
        ts: Date.now(),
      }, ...prev].slice(0, 50));
      setTimeout(fetchStatus, 1500);
    } catch (e: any) {
      setMsg({ ok: false, text: e?.message || "操作失败" });
    } finally {
      setLoading(false);
    }
  };

  const running = status?.running ?? false;
  const tickCount = status?.tick_count ?? 0;
  const successCount = status?.success ?? 0;
  const errorCount = status?.errors ?? 0;

  return (
    <div className="space-y-6 pb-8">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-fg flex items-center gap-2">
            <Zap className="h-5 w-5 text-amber-400" />
            自动操盘
          </h1>
          <p className="text-xs text-fg-muted mt-1">
            策略驱动的全自动交易引擎 · 交互式控制面板
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg ${
            wsStatus === "open"
              ? "bg-pos text-emerald-400"
              : "bg-bg-subtle text-fg-muted"
          }`}>
            <span className={`h-2 w-2 rounded-full ${wsStatus === "open" ? "bg-emerald-500" : "bg-fg-dim"}`} />
            WS {wsStatus === "open" ? "已连接" : "断开"}
          </span>
        </div>
      </div>

      {/* 主控面板 */}
      <div className="grid grid-cols-3 gap-4">
        {/* 控制面板 */}
        <div className="panel-card p-5 col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-fg text-lg font-semibold flex items-center gap-2">
              <Activity className="h-5 w-5 text-emerald-400" />
              交易控制台
            </h2>
            <div className="flex items-center gap-3">
              {running && (
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-sm text-emerald-400 font-medium tabular">
                    运行中 · 第 {tickCount} 轮
                  </span>
                </div>
              )}
              {!running && (
                <span className="text-sm text-fg-muted">待命中</span>
              )}
            </div>
          </div>

          {/* 大按钮 */}
          <div className="flex gap-4 mb-5">
            <button
              onClick={() => doAction("start")}
              disabled={running || loading}
              className={`flex-1 py-4 rounded-xl font-bold text-lg transition flex items-center justify-center gap-3 ${
                running
                  ? "bg-bg-subtle text-fg-muted cursor-not-allowed"
                  : "bg-emerald-500 hover:bg-emerald-400 text-white shadow-lg shadow-emerald-500/20"
              }`}
            >
              <Play className="h-5 w-5" />
              启动自动交易
            </button>
            <button
              onClick={() => doAction("stop")}
              disabled={!running || loading}
              className={`flex-1 py-4 rounded-xl font-bold text-lg transition flex items-center justify-center gap-3 ${
                !running
                  ? "bg-bg-subtle text-fg-muted cursor-not-allowed"
                  : "bg-rose-500 hover:bg-rose-400 text-white shadow-lg shadow-rose-500/20"
              }`}
            >
              <Square className="h-5 w-5" />
              停止交易
            </button>
          </div>

          {/* 扫描间隔 */}
          <div className="flex items-center gap-4 mb-5 p-4 bg-bg-subtle rounded-xl">
            <Clock className="h-5 w-5 text-fg-muted" />
            <div>
              <div className="text-xs text-fg-muted mb-1">扫描间隔（秒）</div>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min={10} max={300} step={10}
                  value={interval}
                  onChange={e => setInterval_s(parseInt(e.target.value))}
                  disabled={running}
                  className="w-48 accent-emerald-500"
                />
                <span className="tabular text-lg font-bold text-fg w-12">{interval}s</span>
              </div>
            </div>
            <div className="flex gap-2 ml-auto">
              {[30, 60, 120, 300].map(v => (
                <button
                  key={v}
                  onClick={() => setInterval_s(v)}
                  disabled={running}
                  className={`px-2.5 py-1 rounded-lg text-xs transition ${
                    interval === v
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/50"
                      : "bg-bg-input text-fg-muted hover:bg-bg-hover border border-line"
                  }`}
                >{v}s</button>
              ))}
            </div>
          </div>

          {/* 提示信息 */}
          {msg && (
            <div className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm mb-4 ${
              msg.ok ? "bg-pos text-emerald-400 border border-emerald-500/30" : "bg-neg text-rose-400 border border-rose-500/30"
            }`}>
              {msg.ok ? <Check className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
              {msg.text}
            </div>
          )}

          {/* 运行指标 */}
          {running && (
            <div className="grid grid-cols-4 gap-3 mt-2">
              <Metric label="已扫描" value={String(tickCount)} icon={<Radio className="h-4 w-4" />} />
              <Metric label="成功" value={String(successCount)} icon={<Check className="h-4 w-4 text-emerald-400" />} />
              <Metric label="异常" value={String(errorCount)} icon={<X className="h-4 w-4 text-rose-400" />} />
              <Metric label="策略" value={status?.strategy || "—"} icon={<Shield className="h-4 w-4" />} />
            </div>
          )}

          {status?.last_error && (
            <div className="mt-3 p-3 bg-neg/50 border border-rose-500/20 rounded-lg text-xs text-rose-400">
              <AlertTriangle className="inline h-3 w-3 mr-1" />
              {status.last_error}
            </div>
          )}
        </div>

        {/* 右侧：账户快照 + 最近订单 */}
        <div className="space-y-4">
          {/* 账户快照 */}
          <div className="panel-card p-5">
            <h2 className="text-fg text-lg font-semibold mb-3 flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-emerald-400" />
              账户快照
            </h2>
            {account ? (
              <div className="space-y-2">
                <Row label="总资产" value={`$${fmtMoney(account.equity)}`} />
                <Row label="可用资金" value={`$${fmtMoney(account.cash)}`} />
                <Row label="持仓市值" value={`$${fmtMoney(account.market_value)}`} />
                <Row label="今日盈亏" value={`${(account.daily_pnl ?? 0) >= 0 ? "+" : ""}$${fmtMoney(account.daily_pnl ?? 0)}`}
                     pos={(account.daily_pnl ?? 0) >= 0} />
                <Row label="持仓数" value={`${account.positions ?? 0} 只`} />
              </div>
            ) : (
              <p className="text-fg-muted text-sm">等待数据…</p>
            )}
          </div>

          {/* 最近订单 */}
          <div className="panel-card p-5">
            <h2 className="text-fg text-lg font-semibold mb-3 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-fg-muted" />
              最近成交
            </h2>
            <div className="space-y-1.5 max-h-48 overflow-auto">
              {orders.slice(0, 8).map(o => (
                <div key={o.order_id} className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-bg-hover text-xs">
                  <div className="flex items-center gap-2">
                    <span className={`font-bold ${o.side === "BUY" ? "text-emerald-400" : "text-rose-400"}`}>
                      {o.side}
                    </span>
                    <span className="text-fg tabular">{o.symbol}</span>
                    <span className="text-fg-muted">×{o.quantity}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-fg-muted tabular">${fmtMoney(o.avg_fill_price)}</span>
                    <span className={`px-1 py-0.5 rounded text-[10px] ${
                      o.status === "filled" ? "bg-pos text-emerald-400" : "bg-neg text-rose-400"
                    }`}>{o.status}</span>
                  </div>
                </div>
              ))}
              {orders.length === 0 && <p className="text-fg-muted text-xs py-4 text-center">暂无成交</p>}
            </div>
          </div>
        </div>
      </div>

      {/* 信号流 */}
      {running && (
        <div className="panel-card p-5">
          <h2 className="text-fg text-lg font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-amber-400" />
            策略信号流
          </h2>
          <div className="space-y-2 max-h-64 overflow-auto">
            {signals.length > 0 && signals.slice(0, 20).map((s, i) => (
              <div key={i} className="flex items-center justify-between px-3 py-2 bg-bg-subtle rounded-lg text-sm">
                <div className="flex items-center gap-3">
                  <span className={`font-bold ${
                    s.action === "BUY" ? "text-emerald-400" : "text-rose-400"
                  }`}>{s.action}</span>
                  <span className="tabular text-fg font-semibold">{s.symbol}</span>
                  <span className="text-xs text-fg-muted">强度 {s.strength?.toFixed(2)}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-fg-muted max-w-xs truncate">{s.reason}</span>
                  <span className="text-xs text-fg-dim tabular">{relTime(s.ts)}</span>
                </div>
              </div>
            ))}
            {signals.length === 0 && running && (
              <div className="flex items-center gap-2 justify-center py-8 text-fg-muted text-sm">
                <RefreshCw className="h-4 w-4 animate-spin" />
                等待第一轮扫描…
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="bg-bg-subtle rounded-lg p-3 text-center">
      <div className="flex justify-center mb-1 text-fg-muted">{icon}</div>
      <div className="tabular text-lg font-bold text-fg">{value}</div>
      <div className="text-[10px] uppercase tracking-wider text-fg-muted mt-0.5">{label}</div>
    </div>
  );
}

function Row({ label, value, pos }: { label: string; value: string; pos?: boolean }) {
  const cls = pos === undefined ? "text-fg" : pos ? "text-emerald-400" : "text-rose-400";
  return (
    <div className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-bg-hover">
      <span className="text-xs text-fg-muted">{label}</span>
      <span className={`tabular text-sm font-semibold ${cls}`}>{value}</span>
    </div>
  );
}
