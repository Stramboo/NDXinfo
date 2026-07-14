import { useTradeStore } from "../store/tradeStore";
import { relTime } from "../lib/utils";
import { cn } from "../lib/utils";

export function Logs() {
  const logs = useTradeStore((s) => s.logs);
  return (
    <section className="panel-card p-0 overflow-hidden">
      <div className="flex items-center justify-between px-5 py-3 border-b border-line">
        <h2 className="text-fg text-lg font-semibold">实时日志</h2>
        <div className="text-fg-muted text-xs tabular">
          {logs.length} 条 · WS 推送
        </div>
      </div>
      <div className="bg-[#0F1117] max-h-[70vh] overflow-auto font-mono text-[12.5px] leading-relaxed">
        {logs.length === 0 ? (
          <div className="p-6 text-fg-muted">
            没有日志，等 tick 推送…
          </div>
        ) : (
          logs.map((l, i) => (
            <div key={i} className="px-5 py-1.5 border-b border-line/40 flex gap-3 items-start">
              <span className="text-fg-dim tabular whitespace-nowrap">
                {new Date(l.ts).toLocaleTimeString("zh-CN")}
              </span>
              <span className={cn(
                "uppercase text-[10px] tracking-wider py-0.5 px-1.5 rounded shrink-0",
                l.level === "ERROR" ? "text-rose-400 bg-neg" :
                l.level === "WARN"  ? "text-amber-400 bg-bg-subtle" :
                l.level === "INFO"  ? "text-emerald-400 bg-pos" :
                                      "text-fg-muted bg-bg-subtle"
              )}>{l.level}</span>
              <span className="text-fg whitespace-pre-wrap break-all">{l.msg}</span>
              {l.context && Object.keys(l.context).length > 0 && (
                <span className="text-fg-muted text-[11px] tabular">
                  {JSON.stringify(l.context)}
                </span>
              )}
            </div>
          ))
        )}
      </div>
    </section>
  );
}
