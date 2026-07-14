import { useTradeStore } from "../store/tradeStore";
import { fmtMoney, fmtPct } from "../lib/utils";

export function PositionsTable() {
  const positions = useTradeStore((s) => s.positions);
  const quotes = useTradeStore((s) => s.quotes);

  // 同步实时报价
  const data = positions.map((p) => {
    const q = quotes[p.symbol];
    const lastPrice = q?.price ?? p.last_price;
    return { ...p, last_price: lastPrice };
  });

  if (data.length === 0) {
    return (
      <div className="h-40 grid place-items-center text-fg-muted text-sm">
        暂无持仓 ·{" "}
        <a className="ml-1 text-emerald-400 hover:underline" href="/trading">去下单</a>
      </div>
    );
  }

  return (
    <table className="w-full text-sm">
      <thead className="text-fg-muted text-[11px] uppercase tracking-wider">
        <tr className="border-b border-line">
          <th className="text-left py-2 px-1">代码</th>
          <th className="text-right py-2 px-1">数量</th>
          <th className="text-right py-2 px-1">成本</th>
          <th className="text-right py-2 px-1">现价</th>
          <th className="text-right py-2 px-1">市值</th>
          <th className="text-right py-2 px-1">浮动盈亏</th>
          <th className="text-right py-2 px-1">%</th>
        </tr>
      </thead>
      <tbody>
        {data.map((p) => {
          const pnl = (p.last_price - p.avg_cost) * p.quantity;
          const pct = p.avg_cost === 0 ? 0 : (p.last_price / p.avg_cost - 1) * 100;
          const positive = pnl >= 0;
          return (
            <tr key={p.symbol} className="border-b border-line/60 hover:bg-bg-hover/50">
              <td className="py-2.5 px-1 font-semibold text-fg">{p.symbol}</td>
              <td className="py-2.5 px-1 text-right tabular text-fg-muted">{p.quantity}</td>
              <td className="py-2.5 px-1 text-right tabular text-fg-muted">
                ${fmtMoney(p.avg_cost, 4)}
              </td>
              <td className="py-2.5 px-1 text-right tabular text-fg">
                ${fmtMoney(p.last_price, 4)}
              </td>
              <td className="py-2.5 px-1 text-right tabular text-fg">
                ${fmtMoney(p.last_price * p.quantity)}
              </td>
              <td className={`py-2.5 px-1 text-right tabular font-semibold ${positive ? "text-emerald-400" : "text-rose-400"}`}>
                {positive ? "+" : ""}${fmtMoney(pnl)}
              </td>
              <td className={`py-2.5 px-1 text-right tabular ${positive ? "text-emerald-400" : "text-rose-400"}`}>
                {fmtPct(pct)}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
