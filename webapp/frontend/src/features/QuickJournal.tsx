/**
 * QuickJournal.tsx --- 快速复盘表单（沙盒卖出后弹出）
 *
 * 从最近一笔 sandbox 交易自动填充 symbol/方向/价格/数量。
 * 用户只需填写交易理由即可保存。
 */

import { useState } from "react";
import { Star, Tag, Send } from "lucide-react";
import { useSandboxStore } from "../store/sandboxStore";
import { fmtMoney } from "../lib/utils";

type Props = {
  onClose: () => void;
  onSaved?: () => void;
};

const RATING_LABELS = ["很差", "较差", "一般", "不错", "很棒"];

export function QuickJournal({ onClose, onSaved }: Props) {
  const orders = useSandboxStore((s) => s.sandboxOrders);
  const lastOrder = orders[0];

  const [rating, setRating] = useState(3);
  const [tags, setTags] = useState("");
  const [notes, setNotes] = useState("");
  const [sending, setSending] = useState(false);
  const [saved, setSaved] = useState(false);

  if (!lastOrder) {
    return (
      <div className="mt-4 p-4 rounded-lg bg-bg-subtle border border-line text-sm text-fg-muted text-center">
        暂无交易记录可供复盘。
        <button onClick={onClose} className="block mx-auto mt-2 text-xs text-emerald-400">关闭</button>
      </div>
    );
  }

  const isBuy = lastOrder.side === "BUY";
  const pnlEstimate = isBuy
    ? null
    : (lastOrder.price - (lastOrder.price * 0.95)) * lastOrder.quantity; // estimate

  async function handleSubmit() {
    if (!notes.trim()) return;
    setSending(true);
    try {
      const res = await fetch("/api/journal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: lastOrder.symbol,
          direction: lastOrder.side === "BUY" ? "long" : "short",
          entry_date: new Date(lastOrder.ts).toISOString().slice(0, 10),
          exit_date: new Date().toISOString().slice(0, 10),
          entry_price: isBuy ? lastOrder.price : lastOrder.price * 0.95,
          exit_price: isBuy ? lastOrder.price * 1.05 : lastOrder.price,
          quantity: lastOrder.quantity,
          notes: `[${"★".repeat(rating)}${"☆".repeat(5 - rating)}] ${tags ? `#${tags} ` : ""}${notes}`,
          rating,
          tags: tags,
        }),
      });
      if (res.ok) {
        setSaved(true);
        onSaved?.();
        setTimeout(onClose, 1200);
      }
    } catch { /* ignore */ }
    setSending(false);
  }

  return (
    <div className="mt-4 p-4 rounded-lg bg-amber-500/5 border border-amber-500/20 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-amber-300">📝 快速复盘</p>
        <button onClick={onClose} className="text-xs text-fg-dim hover:text-fg">✕</button>
      </div>

      {/* Auto-filled trade info */}
      <div className="space-y-1 text-xs text-fg-muted bg-bg-subtle rounded-lg p-3">
        <div className="flex justify-between">
          <span>标的</span>
          <span className="text-fg font-medium">{lastOrder.symbol}</span>
        </div>
        <div className="flex justify-between">
          <span>方向</span>
          <span className={isBuy ? "text-emerald-400" : "text-rose-400"}>
            {isBuy ? "买入" : "卖出"} {lastOrder.quantity} 股 @ ${fmtMoney(lastOrder.price)}
          </span>
        </div>
      </div>

      {/* Rating */}
      <div>
        <p className="text-[10px] uppercase tracking-wider text-fg-muted mb-2">评价</p>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              onClick={() => setRating(n)}
              className={`p-1 rounded transition-colors ${
                n <= rating ? "text-amber-400" : "text-fg-dim hover:text-amber-500/60"
              }`}
              title={RATING_LABELS[n - 1]}
            >
              <Star className="h-4 w-4" fill={n <= rating ? "currentColor" : "none"} />
            </button>
          ))}
          <span className="ml-1 text-xs text-fg-muted">{RATING_LABELS[rating - 1]}</span>
        </div>
      </div>

      {/* Tags */}
      <div>
        <div className="flex items-center gap-1 mb-1">
          <Tag className="h-3 w-3 text-fg-dim" />
          <span className="text-[10px] uppercase tracking-wider text-fg-muted">标签</span>
        </div>
        <input
          type="text"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder="如: 趋势交易, 抄底, 追涨..."
          className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-xs text-fg
                     placeholder:text-fg-dim focus:outline-none focus:border-emerald-500"
        />
      </div>

      {/* Notes */}
      <div>
        <p className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">
          交易理由 <span className="text-rose-400">*</span>
        </p>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="为什么做这笔交易？当时怎么想的？学到了什么？"
          rows={3}
          className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-xs text-fg
                     placeholder:text-fg-dim focus:outline-none focus:border-emerald-500 resize-none"
        />
      </div>

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={!notes.trim() || sending || saved}
        className={`w-full py-2 rounded-lg font-bold text-sm flex items-center justify-center gap-2 transition ${
          saved
            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 cursor-default"
            : "bg-amber-500/90 hover:bg-amber-400 text-bg"
        }`}
      >
        {saved ? "✅ 已保存" : sending ? "保存中..." : (
          <><Send className="h-3.5 w-3.5" /> 保存复盘</>
        )}
      </button>
    </div>
  );
}
