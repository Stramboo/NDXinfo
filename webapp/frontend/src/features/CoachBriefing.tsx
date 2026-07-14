/**
 * CoachBriefing — AI 交易教练每日简报
 */

import { useEffect, useState } from "react";
import {
  Brain, AlertTriangle, Target, Shield,
  GraduationCap, BookOpen,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { fmtMoney } from "../lib/utils";

type BriefingData = {
  headline: string;
  positions: Array<{symbol: string; pnl: number; pnl_pct: number; concentration_pct: number; status: string; advice: string}>;
  warnings: string[];
  opportunities: string[];
  ranking: {
    stats: {total_trades: number; win_rate: number; total_pnl: number};
  };
  tone: string;
};

export function CoachBriefing() {
  const [data, setData] = useState<BriefingData | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetch("/api/coach/briefing")
      .then(r => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="panel-card p-4 animate-pulse">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-bg-subtle" />
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-bg-subtle rounded w-3/4" />
            <div className="h-3 bg-bg-subtle rounded w-1/2" />
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const stats = data.ranking?.stats;
  const hasContent = data.warnings.length > 0 || data.opportunities.length > 0 || data.positions.length > 0;

  const toneBorder = data.tone === "bull"
    ? "border-emerald-500/40"
    : data.tone === "bear"
      ? "border-rose-500/40"
      : "border-amber-500/40";

  const toneBg = data.tone === "bull"
    ? "bg-emerald-500/5"
    : data.tone === "bear"
      ? "bg-rose-500/5"
      : "bg-amber-500/5";

  return (
    <div className={`panel-card overflow-hidden border ${toneBorder} ${toneBg}`}>
      {/* 主标题 */}
      <div className="px-5 pt-4 pb-3">
        <div className="flex items-start gap-3">
          <div className="shrink-0 mt-0.5">
            <div className={`w-9 h-9 rounded-full flex items-center justify-center ${
              data.tone === "bull" ? "bg-emerald-500/20 text-emerald-400" :
              data.tone === "bear" ? "bg-rose-500/20 text-rose-400" :
              "bg-amber-500/20 text-amber-400"
            }`}>
              <Brain className="h-4.5 w-4.5" />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-[15px] leading-relaxed text-fg font-medium">
              {data.headline}
            </div>
            {stats && stats.total_trades > 0 && (
              <div className="flex items-center gap-3 mt-2">
                <span className="text-xs text-fg-muted">
                  胜率 <span className="tabular text-fg">{stats.win_rate}%</span>
                  {" · "}
                  总盈亏 <span className={`tabular ${stats.total_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {stats.total_pnl >= 0 ? "+" : ""}${fmtMoney(Math.abs(stats.total_pnl))}
                  </span>
                </span>
              </div>
            )}
          </div>
        </div>

        {/* 快捷入口 */}
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-line/30">
          <button onClick={() => navigate("/learning")}
                  className="flex items-center gap-1 px-2.5 py-1 rounded text-[10px] text-fg-muted bg-bg-subtle hover:bg-bg-hover hover:text-fg transition">
            <GraduationCap className="h-3 w-3" /> 学习路径
          </button>
          <button onClick={() => navigate("/glossary")}
                  className="flex items-center gap-1 px-2.5 py-1 rounded text-[10px] text-fg-muted bg-bg-subtle hover:bg-bg-hover hover:text-fg transition">
            <BookOpen className="h-3 w-3" /> 术语表
          </button>
        </div>
      </div>

      {/* 详情区（仅在有内容时显示） */}
      {hasContent && (
        <div className="px-5 pb-4 space-y-3">
          {data.warnings.length > 0 && (
            <div className="space-y-1">
              <div className="text-[10px] uppercase tracking-wider text-rose-400 font-medium flex items-center gap-1 mb-1">
                <AlertTriangle className="h-3 w-3" /> 风险提醒
              </div>
              {data.warnings.map((w, i) => (
                <div key={i} className="text-xs text-rose-400/90 bg-rose-500/5 rounded px-3 py-2">{w}</div>
              ))}
            </div>
          )}

          {data.opportunities.length > 0 && (
            <div className="space-y-1">
              <div className="text-[10px] uppercase tracking-wider text-emerald-400 font-medium flex items-center gap-1 mb-1">
                <Target className="h-3 w-3" /> 机会
              </div>
              {data.opportunities.map((o, i) => (
                <div key={i} className="text-xs text-emerald-400/90 bg-emerald-500/5 rounded px-3 py-2">{o}</div>
              ))}
            </div>
          )}

          {data.positions.length > 0 && (
            <div className="space-y-1">
              <div className="text-[10px] uppercase tracking-wider text-fg-muted font-medium flex items-center gap-1 mb-1">
                <Shield className="h-3 w-3" /> 持仓体检
              </div>
              {data.positions.slice(0, 5).map(p => (
                <div key={p.symbol} className="flex items-start gap-3 text-xs bg-bg-subtle rounded-lg px-3 py-2.5">
                  <span className={`shrink-0 mt-0.5 w-2 h-2 rounded-full ${
                    p.status.startsWith("profit") ? "bg-emerald-500" :
                    p.status.startsWith("loss") ? "bg-rose-500" : "bg-fg-dim"
                  }`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-fg tabular">{p.symbol}</span>
                      <span className={`tabular ${p.pnl_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        {p.pnl_pct >= 0 ? "+" : ""}{p.pnl_pct.toFixed(1)}%
                      </span>
                      <span className="text-fg-muted">(占比 {p.concentration_pct}%)</span>
                    </div>
                    <div className="text-fg-muted mt-0.5 leading-relaxed">{p.advice}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
