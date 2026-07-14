import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { KLineChart } from "../features/KLineChart";
import { OrderPanel } from "../features/OrderPanel";
import { OrderHistory } from "../features/OrderHistory";
import { Term } from "../features/InlineTooltip";
import { api } from "../lib/api";
import { fmtMoney } from "../lib/utils";
import { X } from "lucide-react";

const BANNER_KEY = "trading_banner_dismissed";

export function Trading() {
  const [search, setSearch] = useSearchParams();
  const initial = search.get("symbol") || "NVDA";
  const [symbol, setSymbol] = useState(initial);
  const [symbols, setSymbols] = useState<string[]>([]);
  const [quote, setQuote] = useState<{ price: number; ts: number } | null>(null);
  const [showBanner, setShowBanner] = useState(() => !localStorage.getItem(BANNER_KEY));

  const dismissBanner = () => {
    localStorage.setItem(BANNER_KEY, "1");
    setShowBanner(false);
  };

  useEffect(() => {
    api.symbols().then(setSymbols).catch(() => {});
  }, []);

  useEffect(() => {
    let cancelled = false;
    const tick = () => {
      api.quote(symbol).then((q) => {
        if (!cancelled) setQuote(q);
      }).catch(() => {});
    };
    tick();
    const t = setInterval(tick, 2000);
    return () => { cancelled = true; clearInterval(t); };
  }, [symbol]);

  return (
    <div className="grid grid-cols-3 gap-4" style={{ minHeight: "calc(100vh - 4rem - 2rem)" }}>
      {/* 新手提示 banner */}
      {showBanner && (
        <div className="col-span-3 panel-card px-4 py-3 flex items-center gap-3 text-xs border border-emerald-500/20 bg-emerald-500/5">
          <span className="text-emerald-400">💡</span>
          <span className="text-fg-muted flex-1">
            左侧选择股票查看 <Term term="K 线">K线图</Term>，右侧面板用 <Term term="市价单">市价单</Term> 或 <Term term="限价单">限价单</Term> 下单。顶部可用 <Term term="模拟账户">模拟账户</Term> 无风险练习。
          </span>
          <button onClick={dismissBanner} className="text-fg-dim hover:text-fg shrink-0"><X className="h-3.5 w-3.5" /></button>
        </div>
      )}
      {/* 主 K 线 */}
      <section className="panel-card p-5 col-span-2 flex flex-col" style={{ minHeight: 0 }}>
        <div className="flex items-center justify-between mb-4 shrink-0">
          <div className="flex items-center gap-3">
            <SymbolSelect
              symbols={symbols}
              value={symbol}
              onChange={(s) => {
                setSymbol(s);
                setSearch({ symbol: s }, { replace: true });
              }}
            />
            {quote && (
              <div className="tabular text-2xl font-bold text-fg">
                ${fmtMoney(quote.price, 4)}
              </div>
            )}
          </div>
          <div className="text-xs text-fg-muted">
            <a className="hover:text-fg" href="/">← 返回总览</a>
          </div>
        </div>
        <div className="flex-1 min-h-0">
          <KLineChart symbol={symbol} />
        </div>
      </section>

      {/* 下单侧栏 */}
      <section className="panel-card p-5 flex flex-col" style={{ minHeight: 0 }}>
        <h2 className="text-fg text-lg font-semibold mb-4 shrink-0">下单</h2>
        <OrderPanel symbol={symbol} />
        <hr className="my-5 border-line shrink-0" />
        <h3 className="text-fg font-medium mb-3 text-sm shrink-0">最近订单</h3>
        <div className="flex-1 min-h-0 overflow-auto">
          <OrderHistory />
        </div>
      </section>
    </div>
  );
}

function SymbolSelect({
  symbols, value, onChange,
}: { symbols: string[]; value: string; onChange: (s: string) => void }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="bg-bg-input text-fg border border-line rounded-lg px-3 py-2 text-sm font-semibold hover:bg-bg-hover focus:outline-none focus:border-emerald-500"
    >
      {(symbols.length ? symbols : [value]).map((s) => (
        <option key={s} value={s}>{s}</option>
      ))}
    </select>
  );
}
