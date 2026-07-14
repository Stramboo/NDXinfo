import { useTradeStore } from "../store/tradeStore";
import { fmtMoney, relTime } from "../lib/utils";

export function OrderHistory() {
  const orders = useTradeStore((s) => s.orders).slice(0, 50);

  if (orders.length === 0) {
    return (
      <div className="h-32 grid place-items-center text-fg-muted text-sm">
        暂无订单
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      {orders.map((o) => (
        <div key={o.order_id}
             className="bg-bg-subtle rounded-lg p-2.5 text-sm hover:bg-bg-hover transition">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={
                "font-bold " +
                (o.side === "BUY" ? "text-emerald-400" : "text-rose-400")
              }>{o.side}</span>
              <span className="font-semibold text-fg">{o.symbol}</span>
              <span className="tabular text-fg-muted">×{o.quantity}</span>
            </div>
            <span className={
              "text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded " +
              (o.status === "filled"   ? "text-emerald-400 bg-pos" :
               o.status === "rejected" ? "text-rose-400 bg-neg" :
                                          "text-fg-muted bg-bg-input")
            }>{o.status}</span>
          </div>
          <div className="flex items-center justify-between text-xs mt-1">
            <span className="tabular text-fg-muted">${fmtMoney(o.avg_fill_price, 4)}</span>
            <span className="tabular text-fg-dim">{relTime(o.ts)}</span>
          </div>
          {o.note && o.status === "rejected" && (
            <div className="text-[11px] text-rose-400 mt-0.5">{o.note}</div>
          )}
        </div>
      ))}
    </div>
  );
}
