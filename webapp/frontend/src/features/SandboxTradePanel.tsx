/**
 * SandboxTradePanel.tsx --- Mini trading panel for the learning chapter interactive.
 *
 * Uses sandboxStore to buy/sell stocks with the demo account.
 * A simplified version of the main trading panel.
 */

import { useState } from "react";
import { useSandboxStore } from "../store/sandboxStore";
import { fmtMoney } from "../lib/utils";

const AVAILABLE_SYMBOLS = ["NVDA", "AAPL", "TSLA", "MSFT", "GOOGL"];

export function SandboxTradePanel() {
  const cash = useSandboxStore((s) => s.sandboxCash);
  const positions = useSandboxStore((s) => s.sandboxPositions);
  const buyStock = useSandboxStore((s) => s.buyStock);
  const sellStock = useSandboxStore((s) => s.sellStock);

  const [symbol, setSymbol] = useState(AVAILABLE_SYMBOLS[0]);
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [quantity, setQuantity] = useState(10);
  const [price, setPrice] = useState(150);
  const [lastMsg, setLastMsg] = useState<string | null>(null);

  function handleTrade() {
    if (side === "BUY") {
      const cost = quantity * price;
      if (cost > cash) {
        setLastMsg("资金不足，无法完成买入。");
        return;
      }
      buyStock(symbol, quantity, price);
      setLastMsg(`已买入 ${quantity} 股 ${symbol} @ $${fmtMoney(price)}`);
    } else {
      const pos = positions.find((p) => p.symbol === symbol);
      if (!pos || quantity > pos.quantity) {
        setLastMsg("持仓不足，无法完成卖出。");
        return;
      }
      sellStock(symbol, quantity, price);
      setLastMsg(`已卖出 ${quantity} 股 ${symbol} @ $${fmtMoney(price)}`);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-fg-muted">
        在演示账户中练习交易操作。初始资金 $100,000。
      </p>

      {/* Cash display */}
      <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-bg-subtle border border-line">
        <span className="text-xs text-fg-muted">可用资金</span>
        <span className="text-sm font-semibold text-fg tabular">${fmtMoney(cash)}</span>
      </div>

      {/* Symbol selector */}
      <div>
        <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">标的</div>
        <select
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          className="w-full bg-bg-input border border-line rounded-lg px-3 py-2
                     text-sm text-fg focus:outline-none focus:border-emerald-500"
        >
          {AVAILABLE_SYMBOLS.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {/* BUY / SELL */}
      <div className="grid grid-cols-2 rounded-lg overflow-hidden border border-line">
        <button
          onClick={() => setSide("BUY")}
          className={
            "py-2.5 text-sm font-bold transition " +
            (side === "BUY"
              ? "bg-emerald-500 text-bg"
              : "bg-bg-subtle text-fg-muted hover:bg-bg-hover")
          }
        >
          买入
        </button>
        <button
          onClick={() => setSide("SELL")}
          className={
            "py-2.5 text-sm font-bold transition " +
            (side === "SELL"
              ? "bg-rose-500 text-white"
              : "bg-bg-subtle text-fg-muted hover:bg-bg-hover")
          }
        >
          卖出
        </button>
      </div>

      {/* Quantity */}
      <div>
        <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">数量</div>
        <input
          type="number"
          min={1}
          step={1}
          value={quantity}
          onChange={(e) => setQuantity(parseInt(e.target.value || "1", 10))}
          className="w-full bg-bg-input border border-line rounded-lg px-3 py-2
                     text-sm text-fg tabular focus:outline-none focus:border-emerald-500"
        />
      </div>

      {/* Price */}
      <div>
        <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">价格</div>
        <input
          type="number"
          step={0.01}
          min={0.01}
          value={price}
          onChange={(e) => setPrice(parseFloat(e.target.value || "0"))}
          className="w-full bg-bg-input border border-line rounded-lg px-3 py-2
                     text-sm text-fg tabular focus:outline-none focus:border-emerald-500"
        />
      </div>

      {/* Submit */}
      <button
        onClick={handleTrade}
        className={
          "py-2.5 rounded-lg font-bold text-sm transition border " +
          (side === "BUY"
            ? "bg-emerald-500/95 hover:bg-emerald-400 text-bg border-emerald-400"
            : "bg-rose-500/95 hover:bg-rose-400 text-white border-rose-400")
        }
      >
        {side === "BUY" ? `买入 ${quantity} 股` : `卖出 ${quantity} 股`}
      </button>

      {/* Feedback */}
      {lastMsg && (
        <div className="px-3 py-2 rounded-lg bg-bg-subtle border border-line text-sm text-fg-muted">
          {lastMsg}
        </div>
      )}

      {/* Positions summary */}
      {positions.length > 0 && (
        <div className="mt-2">
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-2">
            当前持仓
          </div>
          <div className="space-y-1">
            {positions.map((p) => (
              <div
                key={p.symbol}
                className="flex items-center justify-between text-xs py-1"
              >
                <span className="text-fg font-medium tabular">{p.symbol}</span>
                <span className="text-fg-muted tabular">
                  {p.quantity} 股 @ ${fmtMoney(p.avgCost)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
