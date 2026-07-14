import { useEffect, useState } from "react";
import { useTradeStore } from "../store/tradeStore";
import { fmtMoney } from "../lib/utils";
import { api } from "../lib/api";

export function LiveSymbolsGrid() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const quotes = useTradeStore((s) => s.quotes);
  const [, setSeed] = useState<Record<string, number>>({});

  useEffect(() => {
    api.symbols().then(setSymbols).catch(() => {});
    // 初始报价 — BootstrapData 不会每个 symbol 都拉 quote
    (async () => {
      const out: Record<string, number> = {};
      for (const s of symbols) {
        try { out[s] = (await api.quote(s)).price; }
        catch { /* ignore */ }
      }
      setSeed(out);
    })();
  }, [symbols.length === 0]);

  // 从 account 提取 position-中有的代码，补全 quotes
  const positions = useTradeStore((s) => s.positions);
  const wanted = new Set<string>(symbols);
  for (const p of positions) wanted.add(p.symbol);

  const arr = [...wanted];

  return (
    <div className="grid grid-cols-2 gap-2">
      {arr.map((sym) => {
        const price = quotes[sym]?.price;
        return (
          <a key={sym} href={`/trading?symbol=${sym}`} className="block">
            <div className="bg-bg-subtle hover:bg-bg-hover transition rounded-lg p-3">
              <div className="text-[10px] uppercase tracking-wider text-fg-muted">
                {sym}
              </div>
              <div className="tabular text-lg font-semibold text-fg mt-1">
                {price != null ? `$${fmtMoney(price, 4)}` : "—"}
              </div>
            </div>
          </a>
        );
      })}
    </div>
  );
}
