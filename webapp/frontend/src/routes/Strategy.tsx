import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { fmtPct } from "../lib/utils";
import { Check, AlertCircle } from "lucide-react";

export function Strategy() {
  const [info, setInfo] = useState<{name:string; weights:Record<string,number>; available:string[]} | null>(null);
  const [selected, setSelected] = useState<string>("");
  const [switching, setSwitching] = useState(false);
  const [msg, setMsg] = useState<{ok:boolean; text:string} | null>(null);

  useEffect(() => {
    api.strategy().then((s) => { setInfo(s); setSelected(s.name); }).catch(() => {});
  }, []);

  const switchStrategy = async (name: string) => {
    setSelected(name);
    setSwitching(true);
    setMsg(null);
    try {
      const res = await fetch("/api/strategy", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      }).then(r => r.json());
      setMsg({
        ok: res.applied,
        text: res.applied ? `已切换到「${name}」` : (res.error || "切换失败"),
      });
    } catch (e: any) {
      setMsg({ ok: false, text: e?.message || "切换失败" });
    } finally {
      setSwitching(false);
    }
  };

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
                  onClick={() => switchStrategy(s)}
                  disabled={switching}
                  className={
                    "px-3 py-2 rounded-lg text-sm transition border " +
                    (s === selected
                      ? "bg-emerald-500/10 border-emerald-500 text-emerald-400"
                      : "bg-bg-subtle border-line text-fg-muted hover:bg-bg-hover") +
                    (switching ? " opacity-50 cursor-not-allowed" : "")
                  }
                >
                  {s}
                  {s === selected && switching && (
                    <span className="ml-1.5 inline-block w-3 h-3 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin align-middle" />
                  )}
                </button>
              ))}
            </div>
            {msg && (
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm mb-4 ${
                msg.ok ? "bg-pos text-emerald-400" : "bg-neg text-rose-400"
              }`}>
                {msg.ok ? <Check className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                {msg.text}
              </div>
            )}
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
