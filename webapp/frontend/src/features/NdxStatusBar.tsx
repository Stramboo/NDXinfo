/**
 * NdxStatusBar — Dashboard 顶部的「NDX 大盘状态」横条
 *
 * 数据来源：后端 /api/market/ndx（每 5 分钟缓存）
 * 显示：今日涨跌 / MA200 上下 / RSI / 情绪标签 / 「查看今日报告」按钮
 */

import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Minus, FileText, AlertCircle } from "lucide-react";
import { api } from "../lib/api";

type Ndx = {
  symbol: string;
  last_close: number;
  change_pct: number;
  ma50: number;
  ma200: number;
  above_ma200: boolean;
  rsi14: number;
  sentiment: "bull" | "bear" | "neutral";
  sentiment_label: string;
  summary: string;
  source: "live" | "cached" | "mock";
  ts: number;
  ndx_analysis_report_path: string;
};

const fmt = (v: number, frac = 2) =>
  v.toLocaleString("en-US", { minimumFractionDigits: frac, maximumFractionDigits: frac });
const pct = (v: number, withSign = true) =>
  `${v >= 0 && withSign ? "+" : ""}${v.toFixed(2)}%`;

export function NdxStatusBar() {
  const [data, setData] = useState<Ndx | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        const d = await fetch("/api/market/ndx").then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        });
        if (!cancel) setData(d);
      } catch (e: any) {
        if (!cancel) setErr(e?.message || "拉取 NDX 状态失败");
      }
    })();
    return () => { cancel = true; };
  }, []);

  if (err) return null;     // 完全不渲染，绝不报错
  if (!data) {
    return (
      <div className="panel-card px-4 py-2 text-xs text-fg-muted animate-pulse">
        正在加载 NDX 大盘状态…
      </div>
    );
  }

  const positive = data.change_pct >= 0;
  const Arrow = positive ? TrendingUp : data.change_pct < 0 ? TrendingDown : Minus;
  const colorClass =
    data.sentiment === "bull"  ? "text-emerald-400" :
    data.sentiment === "bear"  ? "text-rose-400" :
                                  "text-fg-muted";
  const bgClass =
    data.sentiment === "bull"  ? "bg-pos" :
    data.sentiment === "bear"  ? "bg-neg" :
                                  "bg-bg-subtle";

  return (
    <div className={"panel-card px-5 py-3 flex items-center gap-4 " + bgClass}>
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wider text-fg-muted">
          NDX 大盘
        </span>
        {data.source === "mock" && (
          <span title="NDX 分析器暂未拉到行情；显示 mock 数据" className="flex items-center gap-1 text-[10px] text-amber-400 bg-bg-subtle px-1.5 py-0.5 rounded">
            <AlertCircle className="h-3 w-3" /> mock
          </span>
        )}
      </div>

      <div className="flex items-baseline gap-2">
        <Arrow className={"h-4 w-4 " + colorClass} />
        <span className={"tabular text-lg font-bold " + colorClass}>
          {pct(data.change_pct)}
        </span>
        <span className="tabular text-sm text-fg-muted">
          ${fmt(data.last_close, 0)}
        </span>
      </div>

      <div className="flex items-center gap-2 text-xs">
        <Pill label="MA200" above={data.above_ma200} value={fmt(data.ma200, 0)} />
        <Pill label="MA50"  above={data.last_close > data.ma50} value={fmt(data.ma50, 0)} />
        <Pill label="RSI"   above={data.rsi14 < 70 && data.rsi14 > 30} value={data.rsi14.toFixed(1)} />
      </div>

      <div className={"px-2 py-1 rounded text-xs font-medium " + bgClass + " " + colorClass}>
        {data.sentiment_label}
      </div>

      <span className="text-xs text-fg-muted truncate flex-1" title={data.summary}>
        {data.summary}
      </span>

      {data.ndx_analysis_report_path && (
        <a
          href={`/${data.ndx_analysis_report_path}`}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1.5 text-xs text-emerald-400 hover:text-emerald-300 bg-bg-subtle hover:bg-bg-hover px-2.5 py-1.5 rounded transition"
        >
          <FileText className="h-3.5 w-3.5" />
          查看今日报告
        </a>
      )}
    </div>
  );
}

function Pill({ label, value, above }: { label: string; value: string; above: boolean }) {
  const cls = above ? "text-emerald-400" : "text-rose-400";
  return (
    <div className="flex items-center gap-1 px-2 py-0.5 bg-bg-subtle rounded">
      <span className="text-[10px] uppercase tracking-wider text-fg-muted">{label}</span>
      <span className={"tabular text-xs " + cls}>{value}</span>
    </div>
  );
}
