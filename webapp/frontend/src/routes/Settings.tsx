import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useTradeStore } from "../store/tradeStore";
import { Sun, Moon, RefreshCw } from "lucide-react";

export function Settings() {
  return (
    <div className="space-y-4 max-w-3xl">
      <Section title="仿真模拟规则" hint="这些规则只对 Mock 引擎生效；真实 Alpaca 由券商方决定。">
        <SimRules />
      </Section>

      <Section title="主题" hint="支持深色 / 浅色两套，目前深色已应用到全站。">
        <Theme />
      </Section>

      <Section title="连接" hint="与后端 WebSocket 实时数据通道。">
        <ConnStatus />
      </Section>
    </div>
  );
}

function Section({ title, hint, children }: {
  title: string; hint?: string; children: React.ReactNode;
}) {
  return (
    <section className="panel-card p-5">
      <h2 className="text-fg text-lg font-semibold">{title}</h2>
      {hint && <p className="text-fg-muted text-sm mt-1">{hint}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}

function SimRules() {
  const [s, setS] = useState<{ slippage_bps: number; commission_per_share: number; t_plus_one: boolean }>({
    slippage_bps: 0, commission_per_share: 0, t_plus_one: false,
  });
  return (
    <div className="grid grid-cols-3 gap-3">
      <Field label="滑点 (bps)" value={s.slippage_bps}
             onChange={(v) => setS({ ...s, slippage_bps: v })} />
      <Field label="每股佣金 ($)" value={s.commission_per_share}
             onChange={(v) => setS({ ...s, commission_per_share: v })} step={0.001} />
      <ToggleField label="启用 T+1" value={s.t_plus_one}
                   onChange={(v) => setS({ ...s, t_plus_one: v })} />
    </div>
  );
}

function Theme() {
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    const saved = localStorage.getItem("ndxinfo.theme");
    return (saved as "dark" | "light") || "dark";
  });
  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
      root.classList.remove("light");
    } else {
      root.classList.add("light");
      root.classList.remove("dark");
    }
    localStorage.setItem("ndxinfo.theme", theme);
  }, [theme]);
  return (
    <div className="flex gap-3">
      <Tile active={theme === "dark"} onClick={() => setTheme("dark")}>
        <Moon className="h-5 w-5 mx-auto mb-2" />
        深色
      </Tile>
      <Tile active={theme === "light"} onClick={() => setTheme("light")}>
        <Sun className="h-5 w-5 mx-auto mb-2" />
        浅色
      </Tile>
    </div>
  );
}

function ConnStatus() {
  const ws = useTradeStore((s) => s.wsStatus);
  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2">
        <span className={
          "h-2 w-2 rounded-full " +
          (ws === "open" ? "bg-emerald-500" : ws === "closed" ? "bg-rose-500" : "bg-amber-500")
        } />
        <span className="text-sm">{ws === "open" ? "已连接" : ws === "closed" ? "已断开 (自动重连)" : "连接中"}</span>
      </div>
      <button
        onClick={() => window.location.reload()}
        className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-fg-muted bg-bg-subtle hover:bg-bg-hover transition"
      >
        <RefreshCw className="h-3.5 w-3.5" /> 刷新
      </button>
    </div>
  );
}

function Field({ label, value, onChange, step }: {
  label: string; value: number; onChange: (v: number) => void; step?: number;
}) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">{label}</div>
      <input
        type="number" value={value} step={step ?? 1}
        onChange={(e) => onChange(parseFloat(e.target.value || "0"))}
        className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-fg tabular focus:outline-none focus:border-emerald-500"
      />
    </div>
  );
}
function ToggleField({ label, value, onChange }: {
  label: string; value: boolean; onChange: (v: boolean) => void;
}) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">{label}</div>
      <button
        onClick={() => onChange(!value)}
        className={
          "w-full py-2 rounded-lg border transition text-sm font-bold " +
          (value
            ? "bg-emerald-500 text-bg border-emerald-500"
            : "bg-bg-input text-fg-muted border-line hover:bg-bg-hover")
        }
      >
        {value ? "已启用" : "关闭"}
      </button>
    </div>
  );
}
function Tile({ active, onClick, children }: {
  active?: boolean; onClick: () => void; children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={
        "flex-1 py-4 rounded-lg border text-sm transition " +
        (active
          ? "bg-emerald-500/10 border-emerald-500 text-emerald-400"
          : "bg-bg-subtle border-line text-fg-muted hover:bg-bg-hover")
      }
    >
      {children}
    </button>
  );
}
