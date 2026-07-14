/**
 * AlertModal — 新建价格告警弹窗
 */

import { useState } from "react";
import { Bell, X, Check } from "lucide-react";
import { api } from "../lib/api";

export function AlertModal({ symbol, onClose, onCreated }: {
  symbol: string;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [condition, setCondition] = useState<"above" | "below">("above");
  const [value, setValue] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    const v = parseFloat(value);
    if (isNaN(v) || v <= 0) return;
    setSubmitting(true);
    try {
      await api.createAlert({ symbol, condition, target_value: v });
      onCreated();
    } catch { /* ignore */ }
    setSubmitting(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="panel-card p-5 w-80" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="flex items-center gap-2 text-fg font-semibold">
            <Bell className="h-4 w-4 text-amber-400" />
            设置告警 · {symbol}
          </h3>
          <button onClick={onClose} className="p-1 rounded text-fg-muted hover:text-fg hover:bg-bg-hover">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-4">
          {/* 条件选择 */}
          <div>
            <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-2">触发条件</div>
            <div className="grid grid-cols-2 gap-2">
              {(["above", "below"] as const).map(c => (
                <button
                  key={c}
                  onClick={() => setCondition(c)}
                  className={`py-2 rounded-lg text-sm font-medium transition border ${
                    condition === c
                      ? "bg-emerald-500/10 border-emerald-500 text-emerald-400"
                      : "bg-bg-subtle border-line text-fg-muted hover:bg-bg-hover"
                  }`}
                >
                  {c === "above" ? "⬆ 突破" : "⬇ 跌破"}
                </button>
              ))}
            </div>
          </div>

          {/* 价格输入 */}
          <div>
            <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-2">目标价格 ($)</div>
            <input
              autoFocus
              type="number"
              step="0.01"
              min="0"
              value={value}
              onChange={e => setValue(e.target.value)}
              onKeyDown={e => e.key === "Enter" && submit()}
              placeholder="例如: 500.00"
              className="w-full bg-bg-input border border-line rounded-lg px-3 py-2.5 text-fg tabular text-lg focus:outline-none focus:border-emerald-500"
            />
          </div>

          <button
            disabled={submitting || !value}
            onClick={submit}
            className="w-full py-2.5 rounded-lg bg-amber-500 text-bg font-bold text-sm hover:bg-amber-400 transition disabled:opacity-50"
          >
            {submitting ? "创建中…" : `当 ${symbol} ${condition === "above" ? "突破" : "跌破"} $${value} 时通知我`}
          </button>
        </div>
      </div>
    </div>
  );
}
