import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { fmtPct } from "../lib/utils";

export function Strategy() {
  const [info, setInfo] = useState<{name:string; weights:Record<string,number>; available:string[]} | null>(null);
  const [selected, setSelected] = useState<string>("");

  useEffect(() => {
    api.strategy().then((s) => { setInfo(s); setSelected(s.name); }).catch(() => {});
  }, []);

  const entries = info ? Object.entries(info.weights) : [];

  return (
    <div className="grid grid-cols-3 gap-4">
      <section className="panel-card p-5 col-span-2">
        <h2 className="text-fg text-lg font-semibold mb-4">当前策略</h2>
        {!info ? (
          <p className="text-fg-muted text-sm">加载中…</p>
        ) : (
          <>
            <div className="flex flex-wrap gap-2 mb-5">
              {info.available.map((s) => (
                <button
                  key={s}
                  onClick={() => setSelected(s)}
                  className={
                    "px-3 py-2 rounded-lg text-sm transition border " +
                    (s === selected
                      ? "bg-emerald-500/10 border-emerald-500 text-emerald-400"
                      : "bg-bg-subtle border-line text-fg-muted hover:bg-bg-hover")
                  }
                >
                  {s}
                </button>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-4 mt-4">
              {entries.length > 0 ? (
                entries.map(([k, v]) => (
                  <div key={k} className="bg-bg-subtle rounded-lg p-3">
                    <div className="text-[10px] uppercase tracking-wider text-fg-muted">
                      {k.toUpperCase()}
                    </div>
                    <div className="mt-1 flex items-baseline gap-2">
                      <div className="tabular text-2xl font-bold text-fg">
                        {fmtPct(v*100, /*withSign*/false)}
                      </div>
                      <div className="text-fg-muted text-sm">权重</div>
                    </div>
                    <div className="mt-2 w-full bg-bg rounded-full h-1.5 overflow-hidden">
                      <div className="bg-emerald-500 h-full" style={{ width: `${v*100}%` }} />
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-fg-muted text-sm col-span-2">
                  该策略没有加权权重。
                </p>
              )}
            </div>
          </>
        )}
      </section>

      <section className="panel-card p-5">
        <h2 className="text-fg text-lg font-semibold mb-4">风控参数</h2>
        <RiskLimits />
      </section>
    </div>
  );
}

function RiskLimits() {
  const [limits, setLimits] = useState<Record<string, any> | null>(null);
  useEffect(() => { api.limits().then(setLimits).catch(() => {}); }, []);
  if (!limits) return <p className="text-fg-muted text-sm">加载中…</p>;
  const rows: [string, string][] = [
    ["max_position_pct",  "最大单仓比"],
    ["stop_loss_pct",     "固定止损"],
    ["trailing_stop_pct", "追踪止损"],
    ["max_daily_trades",  "每日交易上限"],
    ["use_atr_stop",      "启用 ATR 止损"],
  ];
  return (
    <div className="space-y-3">
      {rows.map(([k, lbl]) => (
        <div key={k} className="bg-bg-subtle rounded-lg p-3">
          <div className="text-[10px] uppercase tracking-wider text-fg-muted">
            {lbl}
          </div>
          <div className="tabular text-lg font-semibold text-fg mt-1">
            {typeof limits[k] === "boolean"
              ? limits[k] ? "已启用" : "关闭"
              : String(limits[k])}
          </div>
        </div>
      ))}
    </div>
  );
}
