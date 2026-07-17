/**
 * Learning.tsx — 六阶段学习路线
 *
 * v2.2 重构：从 8 章扁平列表升级为 6 阶段渐变路线图。
 * 数据来源：/api/learning/stages + /api/learning/chapters
 */

import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { GraduationCap, ChevronRight, Lock } from "lucide-react";

type StageData = {
  id: string; title: string; subtitle: string; description: string;
  icon: string; color: string; prerequisite_stage: string | null;
  lessons_total: number; lessons_done: number; unlocked: boolean;
};

type ChapterSummary = {
  id: string; number: number; title: string; summary: string;
  category: string; stage_id: string; completed: boolean; xp: number;
};

const COLOR_MAP: Record<string, string> = {
  emerald: "border-emerald-500/30 bg-emerald-500/5",
  blue: "border-blue-500/30 bg-blue-500/5",
  amber: "border-amber-500/30 bg-amber-500/5",
  purple: "border-purple-500/30 bg-purple-500/5",
  rose: "border-rose-500/30 bg-rose-500/5",
  teal: "border-teal-500/30 bg-teal-500/5",
};

const BAR_COLOR: Record<string, string> = {
  emerald: "bg-emerald-500", blue: "bg-blue-500", amber: "bg-amber-500",
  purple: "bg-purple-500", rose: "bg-rose-500", teal: "bg-teal-500",
};

export function Learning() {
  const [stages, setStages] = useState<StageData[]>([]);
  const [chapters, setChapters] = useState<ChapterSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedStage, setExpandedStage] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetch("/api/learning/stages").then(r => r.ok ? r.json() : null),
      fetch("/api/learning/chapters").then(r => r.ok ? r.json() : null),
    ]).then(([sData, cData]) => {
      if (!cancelled) {
        if (sData?.stages) setStages(sData.stages);
        if (cData?.chapters) setChapters(cData.chapters);
      }
    }).catch(() => {}).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, []);

  // Auto-expand first incomplete stage
  useEffect(() => {
    if (stages.length === 0) return;
    const firstIncomplete = stages.find(s => s.lessons_done < s.lessons_total && s.unlocked);
    if (firstIncomplete) setExpandedStage(firstIncomplete.id);
  }, [stages]);

  const getStageLessons = (stageId: string) =>
    chapters.filter(c => c.stage_id === stageId);

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-fg-muted text-sm">加载中...</div>;
  }

  return (
    <div className="max-w-3xl mx-auto space-y-10 pb-16">
      <div className="space-y-2">
        <div className="flex items-center gap-3 mb-1">
          <GraduationCap className="h-6 w-6 text-fg-muted" />
          <h1 className="text-2xl font-semibold text-fg">学习路径</h1>
        </div>
        <p className="text-sm text-fg-muted">
          六阶段渐进式课程，从零开始理解股票。每节课 5-10 分钟。
        </p>
      </div>

      {/* 6 阶段路线图 */}
      <div className="space-y-4">
        {stages.map((stage, idx) => {
          const lessons = getStageLessons(stage.id);
          const pct = stage.lessons_total > 0
            ? Math.round((stage.lessons_done / stage.lessons_total) * 100) : 0;
          const isExpanded = expandedStage === stage.id;
          const colorClass = COLOR_MAP[stage.color] || COLOR_MAP.emerald;
          const barClass = BAR_COLOR[stage.color] || BAR_COLOR.emerald;

          return (
            <div key={stage.id}>
              {/* 阶段标题卡片 */}
              <button
                onClick={() => stage.unlocked && setExpandedStage(isExpanded ? null : stage.id)}
                disabled={!stage.unlocked}
                className={`w-full text-left rounded-xl border p-5 transition
                  ${stage.unlocked
                    ? `${colorClass} cursor-pointer hover:opacity-80`
                    : "border-line bg-bg-subtle opacity-50 cursor-not-allowed"
                  }`}
              >
                <div className="flex items-start gap-4">
                  <span className="text-2xl shrink-0">{stage.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] uppercase tracking-wider text-fg-dim">
                        阶段 {idx + 1}
                      </span>
                      {pct === 100 && (
                        <span className="text-[10px] text-emerald-400 font-semibold">✓ 完成</span>
                      )}
                    </div>
                    <p className="text-lg font-bold text-fg mt-0.5">{stage.title}</p>
                    <p className="text-xs text-fg-muted mt-1">{stage.subtitle}</p>
                    <p className="text-xs text-fg-dim mt-2 leading-relaxed">{stage.description}</p>

                    {/* 进度条 */}
                    <div className="mt-3 space-y-1">
                      <div className="flex justify-between text-[10px] text-fg-dim">
                        <span>{stage.lessons_done}/{stage.lessons_total} 课</span>
                        <span>{pct}%</span>
                      </div>
                      <div className="h-1 rounded-full bg-bg-subtle overflow-hidden">
                        <div className={`h-full rounded-full transition-all ${barClass}`}
                          style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  </div>
                  {!stage.unlocked ? (
                    <Lock className="w-4 h-4 text-fg-dim shrink-0 mt-1" />
                  ) : (
                    <ChevronRight className={`w-4 h-4 text-fg-dim shrink-0 mt-1 transition-transform
                      ${isExpanded ? "rotate-90" : ""}`} />
                  )}
                </div>
              </button>

              {/* 展开的课时列表 */}
              {isExpanded && stage.unlocked && (
                <div className="ml-8 mt-2 space-y-1 border-l-2 border-line pl-6">
                  {lessons.map((ch) => (
                    <button
                      key={ch.id}
                      onClick={() => navigate(`/learning/${ch.id}`)}
                      className="w-full flex items-center gap-3 px-3 py-3 rounded-lg text-left
                                 hover:bg-bg-hover transition group"
                    >
                      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0
                        ${ch.completed
                          ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-400"
                          : "bg-bg-subtle border border-line text-fg-muted"
                        }`}>
                        {ch.completed ? "✓" : ch.number}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-fg font-medium">{ch.title}</p>
                        <p className="text-xs text-fg-dim line-clamp-1 mt-0.5">{ch.summary}</p>
                      </div>
                      <span className="text-[10px] text-fg-dim tabular">{ch.xp} XP</span>
                      <ChevronRight className="w-3 h-3 text-fg-dim opacity-0 group-hover:opacity-100 transition" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 底部快捷入口 */}
      <div className="flex gap-3">
        <Link to="/learning/dashboard"
          className="text-xs text-fg-dim hover:text-fg transition px-3 py-2 glass-light rounded-[12px] border border-line">
          📊 学习进度 →
        </Link>
        <Link to="/glossary"
          className="text-xs text-fg-dim hover:text-fg transition px-3 py-2 glass-light rounded-[12px] border border-line">
          📖 术语表 →
        </Link>
      </div>
    </div>
  );
}
