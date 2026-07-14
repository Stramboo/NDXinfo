/**
 * OrderPanel — 简洁的下单侧栏（仅市价单 + 限价单两种）
 */

import { useState } from "react";
import { api } from "../lib/api";
import { fmtMoney } from "../lib/utils";

export function OrderPanel({ symbol }: { symbol: string }) {
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [type, setType] = useState<"MARKET" | "LIMIT">("MARKET");
  const [qty, setQty] = useState<number>(10);
  const [limitPrice, setLimitPrice] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [lastOrder, setLastOrder] = useState<{
    status: string;
    note: string;
  } | null>(null);

  const valid = qty > 0 && symbol.length > 0;

  async function submit() {
    if (!valid) return;
    setSubmitting(true);
    setLastOrder(null);
    try {
      const o = await api.placeOrder({
        symbol,
        side,
        quantity: qty,
        order_type: type,
        limit_price: type === "LIMIT" ? limitPrice : null,
      });
      setLastOrder({ status: o.status, note: o.note || `${o.side} ${o.symbol} ×${o.quantity} @ $${fmtMoney(o.avg_fill_price, 4)}` });
    } catch (err: any) {
      setLastOrder({ status: "ERROR", note: err?.message || "下单失败" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* BUY / SELL 切换 */}
      <div className="grid grid-cols-2 rounded-lg overflow-hidden border border-line">
        <button
          onClick={() => setSide("BUY")}
          className={"py-3 text-sm font-bold transition " +
            (side === "BUY"
              ? "bg-emerald-500 text-bg"
              : "bg-bg-subtle text-fg-muted hover:bg-bg-hover")}
        >
          买入 BUY
        </button>
        <button
          onClick={() => setSide("SELL")}
          className={"py-3 text-sm font-bold transition " +
            (side === "SELL"
              ? "bg-rose-500 text-white"
              : "bg-bg-subtle text-fg-muted hover:bg-bg-hover")}
        >
          卖出 SELL
        </button>
      </div>

      {/* 限价单/市价单 */}
      <div className="grid grid-cols-2 rounded-lg overflow-hidden border border-line text-xs">
        {(["MARKET", "LIMIT"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setType(t)}
            className={"py-2 transition " +
              (type === t
                ? "bg-bg-hover text-fg"
                : "bg-bg-subtle text-fg-muted hover:bg-bg-hover")}
          >
            {t === "MARKET" ? "市价单" : "限价单"}
          </button>
        ))}
      </div>

      {/* 数量 */}
      <Field label="数量">
        <input
          type="number" min={1} step={1}
          value={qty}
          onChange={(e) => setQty(parseInt(e.target.value || "0", 10))}
          className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-fg tabular focus:outline-none focus:border-emerald-500"
        />
        <div className="grid grid-cols-4 gap-1 mt-2 text-xs">
          {[10, 50, 100, 500].map((q) => (
            <button
              key={q} onClick={() => setQty(q)}
              className="bg-bg-subtle hover:bg-bg-hover text-fg-muted rounded py-1 transition"
            >
              {q}
            </button>
          ))}
        </div>
      </Field>

      {type === "LIMIT" && (
        <Field label="限价">
          <input
            type="number" step={0.01} min={0}
            value={limitPrice ?? ""}
            onChange={(e) => setLimitPrice(e.target.value === "" ? null : parseFloat(e.target.value))}
            className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-fg tabular focus:outline-none focus:border-emerald-500"
          />
        </Field>
      )}

      <button
        disabled={!valid || submitting}
        onClick={submit}
        className={
          "py-3 rounded-lg font-bold transition border " +
          (side === "BUY"
            ? "bg-emerald-500/95 hover:bg-emerald-400 text-bg border-emerald-400"
            : "bg-rose-500/95   hover:bg-rose-400   text-white border-rose-400") +
          (submitting || !valid ? " opacity-50 cursor-not-allowed" : "")
        }
      >
        {submitting ? "下单中…" : `确认 ${side === "BUY" ? "买入" : "卖出"} ${qty} 股`}
      </button>

      {lastOrder && (
        <div
          className={
            "rounded-lg p-3 text-sm border " +
            (lastOrder.status === "filled"
              ? "border-emerald-500/50 bg-emerald-500/5 text-emerald-400"
              : lastOrder.status === "rejected" || lastOrder.status === "ERROR"
                ? "border-rose-500/50 bg-rose-500/5 text-rose-400"
                : "border-line bg-bg-subtle text-fg")
          }
        >
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">
            {lastOrder.status === "filled"
              ? "✓ 已成交"
              : lastOrder.status === "rejected"
                ? "✗ 已拒绝"
                : "结果"}
          </div>
          {lastOrder.note}
        </div>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">
        {label}
      </div>
      {children}
    </div>
  );
}
