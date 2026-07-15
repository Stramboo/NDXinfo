/**
 * CoachReview.tsx — AI 教练结构化反馈卡片
 *
 * 展示交易四维评估：决策 / 执行 / 风险 / 归因。
 * 支持可选的 LLM 点评。
 */

import { useState } from "react";

interface CategoryData {
  score: number;
  summary: string;
  breakdown: { item: string; score: number; note: string }[];
}

interface CoachResult {
  overall: number;
  grade: string;
  decision: CategoryData;
  execution: CategoryData;
  risk: CategoryData;
  attribution: CategoryData;
  highlights: string[];
  improvements: string[];
  llm_comment: string;
}

interface CoachReviewProps {
  result: CoachResult;
  onClose: () => void;
}

const GRADE_COLORS: Record<string, string> = {
  S: "text-amber-400 bg-amber-500/10 border-amber-500/30",
  A: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
  B: "text-blue-400 bg-blue-500/10 border-blue-500/30",
  C: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
  D: "text-rose-400 bg-rose-500/10 border-rose-500/30",
};

function ScoreBar({ score, label }: { score: number; label: string }) {
  const pct = Math.min(score, 100);
  const color =
    pct >= 80 ? "bg-emerald-500" : pct >= 60 ? "bg-blue-500" : pct >= 40 ? "bg-yellow-500" : "bg-rose-500";

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-fg-muted">{label}</span>
        <span className="text-fg font-semibold tabular">{score}</span>
      </div>
      <div className="h-1.5 rounded-full bg-bg-input overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function CategoryPanel({ data }: { data: CategoryData }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border border-line rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-2.5 bg-bg-subtle hover:bg-bg-hover transition text-sm"
      >
        <span className="font-medium text-fg">{data.summary}</span>
        <span className={`text-xs tabular ${open ? "rotate-90" : ""} transition-transform`}>
          ▶
        </span>
      </button>
      {open && (
        <div className="px-3 py-2 space-y-1.5 border-t border-line">
          {data.breakdown.map((item, i) => (
            <div key={i} className="flex justify-between text-xs">
              <span className="text-fg-muted">{item.item}</span>
              <span className="text-fg-dim tabular">
                {item.score > 0 ? `+${item.score}` : item.score} · {item.note}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function CoachReview({ result, onClose }: CoachReviewProps) {
  const gradeStyle = GRADE_COLORS[result.grade] ?? GRADE_COLORS.D;

  return (
    <div className="mt-2 p-4 rounded-xl bg-bg-subtle border border-line space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl font-black border ${gradeStyle}`}>
            {result.grade}
          </div>
          <div>
            <div className="text-sm font-bold text-fg">AI 教练评估</div>
            <div className="text-xs text-fg-muted">综合得分 {result.overall} / 100</div>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-fg-dim hover:text-fg transition text-lg leading-none"
        >
          ×
        </button>
      </div>

      {/* LLM Comment */}
      {result.llm_comment && (
        <div className="p-3 rounded-lg bg-blue-500/5 border border-blue-500/20 text-xs text-fg-muted leading-relaxed">
          💬 {result.llm_comment}
        </div>
      )}

      {/* Score Bars */}
      <div className="space-y-2">
        <ScoreBar score={result.decision.score} label="决策质量" />
        <ScoreBar score={result.execution.score} label="执行质量" />
        <ScoreBar score={result.risk.score} label="风险管理" />
        <ScoreBar score={result.attribution.score} label="结果归因" />
      </div>

      {/* Category Details */}
      <div className="space-y-1.5">
        <CategoryPanel data={result.decision} />
        <CategoryPanel data={result.execution} />
        <CategoryPanel data={result.risk} />
        <CategoryPanel data={result.attribution} />
      </div>

      {/* Highlights & Improvements */}
      <div className="grid grid-cols-2 gap-3">
        {result.highlights.length > 0 && (
          <div className="space-y-1">
            <div className="text-[10px] uppercase tracking-wider text-emerald-400 font-semibold">亮点</div>
            {result.highlights.map((h, i) => (
              <div key={i} className="text-xs text-fg-muted leading-relaxed">✅ {h}</div>
            ))}
          </div>
        )}
        {result.improvements.length > 0 && (
          <div className="space-y-1">
            <div className="text-[10px] uppercase tracking-wider text-rose-400 font-semibold">改进</div>
            {result.improvements.map((imp, i) => (
              <div key={i} className="text-xs text-fg-muted leading-relaxed">⚠️ {imp}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
