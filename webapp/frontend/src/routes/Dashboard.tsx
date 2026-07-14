import { useTradeStore } from "../store/tradeStore";
import { usePreferenceStore } from "../store/preferenceStore";
import { fmtMoney, fmtPct, relTime } from "../lib/utils";
import { ArrowUpRight, ArrowDownRight, Wallet, Briefcase, Activity, ListChecks } from "lucide-react";
import { EquityCurve } from "../features/EquityCurve";
import { PositionsTable } from "../features/PositionsTable";
import { LiveSymbolsGrid } from "../features/LiveSymbolsGrid";
import { NdxStatusBar } from "../features/NdxStatusBar";
import { WatchlistPanel } from "../features/WatchlistPanel";
import { CoachBriefing } from "../features/CoachBriefing";

export function Dashboard() {
  const account = useTradeStore((s) => s.account);
  const orders = useTradeStore((s) => s.orders);
  const signals = useTradeStore((s) => s.signals);
  const { dashboardLayout } = usePreferenceStore();
  const hidden = dashboardLayout.hiddenPanels;

  const totalReturn = account?.total_return_pct ?? 0;
  const dailyPnl = account?.daily_pnl ?? 0;
  return (
    <div className="space-y-6 pb-8">
      {/* AI 教练每日简报 */}
      <CoachBriefing />

      {/* NDX 大盘状态（精简） */}
      {!hidden.includes("ndx-status") && <NdxStatusBar />}

      {/* 大数字卡片 */}
      {!hidden.includes("account-cards") && (
        <div className="grid grid-cols-4 gap-4">
          <Card
            label="账户净值" value={`$${fmtMoney(account?.equity ?? 0)}`}
            delta={fmtPct(totalReturn)} pos={totalReturn >= 0}
            icon={<Wallet className="h-5 w-5" />}
          />
          <Card
            label="持仓市值" value={`$${fmtMoney(account?.market_value ?? 0)}`}
            sub={`${account?.positions ?? 0} 个标的`}
            icon={<Briefcase className="h-5 w-5" />}
          />
          <Card
            label="今日盈亏" value={`${dailyPnl >= 0 ? "+" : ""}$${fmtMoney(dailyPnl)}`}
            delta={fmtPct(account?.total_return_pct ?? 0, false)} pos={dailyPnl >= 0}
            icon={dailyPnl >= 0 ? <ArrowUpRight className="h-5 w-5" /> : <ArrowDownRight className="h-5 w-5" />}
          />
          <Card
            label="信号活动" value={`${signals.length}`}
            sub={`过去 ${signals[0] ? relTime(signals[0].ts) : "—"} 收到 ${signals[0]?.action ?? "—"}`}
            icon={<Activity className="h-5 w-5" />}
          />
        </div>
      )}

      {/* 净值曲线 */}
      {!hidden.includes("equity-curve") && (
        <section className="panel-card p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-fg text-lg font-semibold">净值曲线</h2>
              <p className="text-fg-muted text-sm">最近 {Math.min(400, useTradeStore.getState().equityHistory.length)} 个 tick</p>
            </div>
            <div className="flex gap-2 text-xs">
              <Pill label="1m" active /><Pill label="5m" /><Pill label="1h" /><Pill label="1d" />
            </div>
          </div>
          <EquityCurve />
        </section>
      )}

      {/* 持仓 + 自选 + 实时报价 */}
      <div className="grid grid-cols-3 gap-4">
        {!hidden.includes("positions") && (
          <section className="panel-card p-5 col-span-2">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-fg text-lg font-semibold flex items-center gap-2">
                <ListChecks className="h-5 w-5" /> 当前持仓
              </h2>
            </div>
            <PositionsTable />
          </section>
        )}

        {/* 自选列表 或 实时报价 */}
        {!hidden.includes("watchlist") && (
          <WatchlistPanel />
        )}
        {hidden.includes("watchlist") && !hidden.includes("live-quotes") && (
          <section className="panel-card p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-fg text-lg font-semibold">实时报价</h2>
            </div>
            <LiveSymbolsGrid />
          </section>
        )}
        {!hidden.includes("positions") && !hidden.includes("live-quotes") && !hidden.includes("watchlist") ? (
          <section className="panel-card p-5">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-fg text-lg font-semibold">实时报价</h2>
            </div>
            <LiveSymbolsGrid />
          </section>
        ) : null}
      </div>

      {/* 最近订单 / 信号 */}
      <div className="grid grid-cols-2 gap-4">
        {!hidden.includes("recent-orders") && (
          <section className="panel-card p-5">
            <h2 className="text-fg text-lg font-semibold mb-3">最近订单</h2>
            {orders.length === 0 ? (
              <Empty text="还没有订单；下单试试看" />
            ) : (
              <div className="space-y-2">
                {orders.slice(0, 8).map((o) => (
                  <div key={o.order_id} className="flex items-center justify-between text-sm border-b border-line last:border-b-0 py-2">
                    <div className="flex items-center gap-2">
                      <span className={o.side === "BUY" ? "text-emerald-400" : "text-rose-400"}>{o.side}</span>
                      <span className="tabular text-fg">{o.symbol}</span>
                      <span className="text-fg-muted tabular">× {o.quantity}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="tabular text-fg-muted">${fmtMoney(o.avg_fill_price)}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                        o.status === "filled" ? "bg-pos text-emerald-400" :
                        o.status === "rejected" ? "bg-neg text-rose-400" : "bg-bg-subtle text-fg-muted"
                      }`}>{o.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {!hidden.includes("recent-signals") && (
          <section className="panel-card p-5">
            <h2 className="text-fg text-lg font-semibold mb-3">最近信号</h2>
            {signals.length === 0 ? (
              <Empty text="没有信号" />
            ) : (
              <div className="space-y-2">
                {signals.slice(0, 8).map((s, i) => (
                  <div key={i} className="flex items-start justify-between border-b border-line last:border-b-0 py-2 text-sm">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`font-semibold ${
                          s.action === "BUY" ? "text-emerald-400" :
                          s.action === "SELL" ? "text-rose-400" : "text-fg-muted"
                        }`}>{s.action}</span>
                        <span className="text-fg tabular">{s.symbol}</span>
                      </div>
                      <div className="text-fg-muted text-xs mt-0.5">{s.reason}</div>
                    </div>
                    <div className="tabular text-xs text-fg-muted self-end">{relTime(s.ts)}</div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  );
}

function Card({ label, value, delta, sub, pos, icon }: {
  label: string; value: string; delta?: string; sub?: string; pos?: boolean; icon: React.ReactNode;
}) {
  return (
    <div className="panel-card p-5">
      <div className="flex items-center justify-between">
        <div className="text-[11px] uppercase tracking-wider text-fg-muted">{label}</div>
        <div className="text-fg-muted">{icon}</div>
      </div>
      <div className="mt-3 tabular text-2xl font-bold text-fg">{value}</div>
      {(delta || sub) && (
        <div className="mt-1 flex items-center gap-2 text-sm">
          {delta && <span className={`tabular ${pos ? "text-emerald-400" : "text-rose-400"}`}>{delta}</span>}
          {sub && <span className="text-fg-muted">{sub}</span>}
        </div>
      )}
    </div>
  );
}

function Pill({ label, active }: { label: string; active?: boolean }) {
  return (
    <button className={"px-2.5 py-1 rounded-md transition " +
      (active ? "bg-emerald-500 text-bg" : "bg-bg-subtle text-fg-muted hover:bg-bg-hover")}>{label}</button>
  );
}

function Empty({ text }: { text: string }) {
  return <div className="h-32 grid place-items-center text-fg-muted text-sm">{text}</div>;
}
