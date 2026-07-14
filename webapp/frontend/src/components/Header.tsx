import { useTradeStore } from "../store/tradeStore";
import { useSandboxStore } from "../store/sandboxStore";
import { DemoAccountSwitch } from "../features/DemoAccountSwitch";
import { fmtMoney, fmtPct } from "../lib/utils";

export function Header() {
  const realAccount = useTradeStore((s) => s.account);
  const isSimulation = useSandboxStore((s) => s.isSimulationMode);
  const sandboxCash = useSandboxStore((s) => s.sandboxCash);
  const sandboxPositions = useSandboxStore((s) => s.sandboxPositions);

  const account = isSimulation
    ? {
        equity: sandboxCash + sandboxPositions.reduce((s, p) => s + p.quantity * p.avgCost, 0),
        cash: sandboxCash,
        daily_pnl: 0,
        total_return_pct: 0,
      }
    : realAccount;

  return (
    <header className="h-16 shrink-0 bg-bg-panel border-b border-line flex items-center px-6">
      <div className="flex-1">
        <DemoAccountSwitch />
      </div>
      <div className="flex items-center gap-8">
        <Stat label="总资产" value={`$${fmtMoney(account?.equity ?? 0)}`} pos={true} />
        <Stat label="可用资金" value={`$${fmtMoney(account?.cash ?? 0)}`} />
        <Stat label="今日盈亏"
              value={`${(account?.daily_pnl ?? 0) >= 0 ? "+" : ""}$${fmtMoney(account?.daily_pnl ?? 0)}`}
              pos={(account?.daily_pnl ?? 0) >= 0}
        />
        <Stat label="总收益率" value={fmtPct(account?.total_return_pct ?? 0)}
              pos={(account?.total_return_pct ?? 0) >= 0} />
      </div>
    </header>
  );
}

function Stat({
  label, value, pos,
}: { label: string; value: string; pos?: boolean }) {
  const vColor = pos === undefined
    ? "text-fg"
    : pos
      ? "text-emerald-400"
      : "text-rose-400";
  return (
    <div className="flex flex-col items-end">
      <div className="text-[10px] uppercase tracking-wider text-fg-muted">
        {label}
      </div>
      <div className={`tabular text-base font-semibold ${vColor}`}>
        {value}
      </div>
    </div>
  );
}
