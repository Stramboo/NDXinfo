/**
 * SandboxTradePanel.tsx --- Mini trading panel for the learning chapter interactive.
 *
 * Uses sandboxStore to buy/sell stocks with the demo account.
 * Prices come from the backend /api/market/batch (real market data).
 * A simplified version of the main trading panel.
 */

import { useState, useEffect, useCallback } from "react";
import { useSandboxStore } from "../store/sandboxStore";
import { fmtMoney } from "../lib/utils";
import { QuickJournal } from "./QuickJournal";

const AVAILABLE_SYMBOLS = ["NVDA", "AAPL", "TSLA", "MSFT", "GOOGL"];
const REFRESH_INTERVAL_MS = 30_000; // 30 秒轮询刷新价格

export function SandboxTradePanel() {
  const cash = useSandboxStore((s) => s.sandboxCash);
  const positions = useSandboxStore((s) => s.sandboxPositions);
  const orders = useSandboxStore((s) => s.sandboxOrders);
  const buyStock = useSandboxStore((s) => s.buyStock);
  const sellStock = useSandboxStore((s) => s.sellStock);
  const updatePrices = useSandboxStore((s) => s.updatePrices);

  const [symbol, setSymbol] = useState(AVAILABLE_SYMBOLS[0]);
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [quantity, setQuantity] = useState(10);
  const [prices, setPrices] = useState<Record<string, number>>({});
  const [pricesLoading, setPricesLoading] = useState(true);
  const [lastMsg, setLastMsg] = useState<string | null>(null);
  const [showReviewPrompt, setShowReviewPrompt] = useState(false);

  // ---- 从后端获取真实价格 ----
  const fetchPrices = useCallback(async () => {
    try {
      const res = await fetch(
        `/api/market/batch?symbols=${AVAILABLE_SYMBOLS.join(",")}`,
      );
      if (!res.ok) return;
      const data = await res.json();
      if (data?.prices) {
        setPrices(data.prices);
        updatePrices(data.prices);
        setPricesLoading(false);
      }
    } catch {
      // 网络错误时保持上次价格
    }
  }, [updatePrices]);

  useEffect(() => {
    fetchPrices();
    const timer = setInterval(fetchPrices, REFRESH_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [fetchPrices]);

  const currentPrice = prices[symbol];

  function handleTrade() {
    if (currentPrice == null) {
      setLastMsg("价格尚未加载，请稍候再试。");
      return;
    }
    if (side === "BUY") {
      const cost = quantity * currentPrice;
      if (cost > cash) {
        setLastMsg("资金不足，无法完成买入。");
        return;
      }
      buyStock(symbol, quantity, currentPrice);
      setLastMsg(`已买入 ${quantity} 股 ${symbol} @ $${fmtMoney(currentPrice)}`);
    } else {
      const pos = positions.find((p) => p.symbol === symbol);
      if (!pos || quantity > pos.quantity) {
        setLastMsg("持仓不足，无法完成卖出。");
        return;
      }
      sellStock(symbol, quantity, currentPrice);
      setLastMsg(`已卖出 ${quantity} 股 ${symbol} @ $${fmtMoney(currentPrice)}`);
      setShowReviewPrompt(true);
    }
  }

  // 计算总市值（用于盈亏展示）
  const marketValue = positions.reduce(
    (sum, p) => sum + p.quantity * (prices[p.symbol] ?? p.avgCost),
    0,
  );
  const totalEquity = cash + marketValue;
  const totalPnl = totalEquity - 100_000;

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-fg-muted">
        在演示账户中练习交易操作。初始资金 $100,000，价格来自真实行情。
      </p>

      {/* Account summary */}
      <div className="space-y-1 px-3 py-2 rounded-lg bg-bg-subtle border border-line text-xs">
        <div className="flex justify-between">
          <span className="text-fg-muted">可用资金</span>
          <span className="text-fg font-semibold tabular">${fmtMoney(cash)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-fg-muted">持仓市值</span>
          <span className="text-fg tabular">${fmtMoney(marketValue)}</span>
        </div>
        <div className="flex justify-between border-t border-line pt-1 mt-1">
          <span className="text-fg-muted">总资产</span>
          <span className="text-fg font-semibold tabular">${fmtMoney(totalEquity)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-fg-muted">总盈亏</span>
          <span className={`tabular font-medium ${totalPnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
            {totalPnl >= 0 ? "+" : ""}{fmtMoney(totalPnl)}
          </span>
        </div>
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

      {/* Price (read-only, from real market) */}
      <div>
        <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">
          价格 <span className="normal-case text-fg-dim">· 实时行情</span>
        </div>
        {pricesLoading ? (
          <div className="w-full px-3 py-2 rounded-lg bg-bg-input border border-line text-sm text-fg-dim animate-pulse">
            价格加载中...
          </div>
        ) : currentPrice != null ? (
          <div className="w-full px-3 py-2 rounded-lg bg-bg-input border border-line text-lg font-bold text-fg tabular">
            ${fmtMoney(currentPrice)}
          </div>
        ) : (
          <div className="w-full px-3 py-2 rounded-lg bg-bg-input border border-line text-sm text-amber-400">
            价格暂不可用
          </div>
        )}
      </div>

      {/* Estimated cost/revenue */}
      {currentPrice != null && (
        <div className="px-3 py-1.5 rounded-lg bg-bg-subtle text-xs text-fg-muted text-center">
          预计{side === "BUY" ? "花费" : "收入"}：<span className="text-fg font-semibold tabular">${fmtMoney(quantity * currentPrice)}</span>
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleTrade}
        disabled={pricesLoading || currentPrice == null}
        className={
          "py-2.5 rounded-lg font-bold text-sm transition border " +
          (side === "BUY"
            ? "bg-emerald-500/95 hover:bg-emerald-400 text-bg border-emerald-400"
            : "bg-rose-500/95 hover:bg-rose-400 text-white border-rose-400") +
          (pricesLoading || currentPrice == null ? " opacity-50 cursor-not-allowed" : "")
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

      {/* Review prompt after selling */}
      {showReviewPrompt && (
        <QuickJournal
          onClose={() => setShowReviewPrompt(false)}
          onSaved={() => {
            // Attempt to complete journal quest
            fetch("/api/learning/quests/check", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                quest_id: "q0402",
                context: { journal_count: 1 },
              }),
            }).catch(() => {});
          }}
        />
      )}

      {/* Positions summary */}
      {positions.length > 0 && (
        <div className="mt-2">
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-2">
            当前持仓
          </div>
          <div className="space-y-1">
            {positions.map((p) => {
              const curPx = prices[p.symbol] ?? p.avgCost;
              const posPnl = (curPx - p.avgCost) * p.quantity;
              return (
                <div
                  key={p.symbol}
                  className="flex items-center justify-between text-xs py-1"
                >
                  <span className="text-fg font-medium tabular">{p.symbol}</span>
                  <span className="text-fg-muted tabular">{p.quantity} 股</span>
                  <span className={`tabular ${posPnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {posPnl >= 0 ? "+" : ""}{fmtMoney(posPnl)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
