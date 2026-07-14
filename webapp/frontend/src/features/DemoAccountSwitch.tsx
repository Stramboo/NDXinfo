/**
 * DemoAccountSwitch.tsx --- Clean pill-toggle in the header area
 * for switching between real account and demo/simulated account.
 */

import { useSandboxStore } from "../store/sandboxStore";
import { cn } from "../lib/utils";

export function DemoAccountSwitch() {
  const isSimulation = useSandboxStore((s) => s.isSimulationMode);
  const setIsSimulation = useSandboxStore((s) => s.setIsSimulationMode);

  const shared =
    "px-3 py-1 text-xs font-medium rounded-md transition-colors tracking-wide";

  return (
    <div className="flex items-center rounded-lg bg-bg-subtle border border-line overflow-hidden">
      <button
        onClick={() => setIsSimulation(false)}
        className={cn(
          shared,
          !isSimulation
            ? "bg-emerald-500 text-bg"
            : "text-fg-muted hover:text-fg",
        )}
      >
        真实账户
      </button>
      <button
        onClick={() => setIsSimulation(true)}
        className={cn(
          shared,
          isSimulation
            ? "bg-amber-500 text-bg"
            : "text-fg-muted hover:text-fg",
        )}
      >
        模拟账户
      </button>
    </div>
  );
}
