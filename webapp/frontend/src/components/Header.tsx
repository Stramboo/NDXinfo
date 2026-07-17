/**
 * Header.tsx — Liquid Glass 浮动玻璃顶栏
 *
 * macOS 27 风格：浮动玻璃胶囊，显示模拟账户余额
 */
import { useSandboxStore } from "../store/sandboxStore";

export function Header() {
  const sandboxCash = useSandboxStore((s) => s.sandboxCash);
  const sandboxPositions = useSandboxStore((s) => s.sandboxPositions);
  const marketValue = sandboxPositions.reduce((s, p) => s + p.quantity * p.avgCost, 0);

  return (
    <header className="relative z-10 shrink-0 flex items-center justify-end px-6 pt-3 pb-1">
      {/* 浮动玻璃胶囊 */}
      <div className="glass-pill rounded-full px-4 py-2 flex items-center gap-2">
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400
                         shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
        <span className="text-xs text-fg-muted">模拟账户</span>
        <span className="text-sm text-fg font-semibold tabular">
          ${(sandboxCash + marketValue).toLocaleString()}
        </span>
      </div>
    </header>
  );
}
