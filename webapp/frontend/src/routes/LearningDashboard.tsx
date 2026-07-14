/**
 * LearningDashboard.tsx --- 学习进度仪表盘
 *
 * 数据来源: /api/learning/progress/dashboard
 * 布局: 等级卡片 + XP 进度 + 章节环形进度 + 统计数据
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BarChart3, Flame, BookOpen, CheckCircle, ChevronRight } from "lucide-react";

type ChapterSummary = {
  id: string; number: number; title: string; category: string;
  completed: boolean; quests_done: number; quests_total: number;
};

type DashboardData = {
  chapters_completed: number;
  chapters_total: number;
  quests_completed: number;
  quests_total: number;
  total_xp: number;
  level: string;
  next_level_xp: number;
  streak_days: number;
  chapters: ChapterSummary[];
};

const LEVEL_PREV_XP: Record<string, number> = {
  "学徒": 0, "见习": 100, "初级": 300, "中级": 800,
  "高级": 2000, "专家": 5000, "大师": 10000,
};
const LEVEL_COLORS: Record<string, string> = {
  "学徒": "#CD7F32", "见习": "#A0A0A0", "初级": "#6B8E23",
  "中级": "#3B82F6", "高级": "#8B5CF6", "专家": "#F59E0B", "大师": "#EF4444",
};

const CATEGORY_COLORS: Record<string, string> = {
  "基础": "bg-sky-500", "操作": "bg-amber-500", "进阶": "bg-violet-500",
};

export function LearningDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetch("/api/learning/progress/dashboard")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d) setData(d);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-fg-muted text-sm">加载中...</div>;
  }

  if (!data) {
    return <div className="flex items-center justify-center h-64 text-fg-muted text-sm">数据加载失败</div>;
  }

  const prevXp = LEVEL_PREV_XP[data.level] || 0;
  const xpInLevel = data.total_xp - prevXp;
  const xpNeeded = data.next_level_xp - prevXp;
  const xpPct = Math.min(100, Math.round((xpInLevel / xpNeeded) * 100));
  const levelColor = LEVEL_COLORS[data.level] || "#6B7280";

  // Group chapters by category
  const categories = ["基础", "操作", "进阶"];
  const grouped = categories.map((cat) => ({
    category: cat,
    chapters: data.chapters.filter((c) => c.category === cat),
  }));

  return (
    <div className="max-w-5xl mx-auto space-y-10 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-1">
          <BarChart3 className="h-6 w-6 text-fg-muted" />
          <h1 className="text-2xl font-semibold text-fg tracking-tight">学习进度</h1>
        </div>
        <p className="text-sm text-fg-muted mt-1">追踪你的学习历程和成就。</p>
      </div>

      {/* Top stats row */}
      <div className="grid grid-cols-4 gap-4">
        <div className="panel-card p-4 text-center">
          <p className="text-[10px] uppercase tracking-wider text-fg-dim mb-1">等级</p>
          <p className="text-2xl font-bold" style={{ color: levelColor }}>{data.level}</p>
        </div>
        <div className="panel-card p-4 text-center">
          <p className="text-[10px] uppercase tracking-wider text-fg-dim mb-1">经验值</p>
          <p className="text-2xl font-bold text-fg tabular">{data.total_xp}</p>
          <p className="text-xs text-fg-muted mt-0.5">XP</p>
        </div>
        <div className="panel-card p-4 text-center">
          <p className="text-[10px] uppercase tracking-wider text-fg-dim mb-1">连续学习</p>
          <div className="flex items-center justify-center gap-1.5">
            <Flame className="h-5 w-5 text-amber-400" />
            <span className="text-2xl font-bold text-fg tabular">{data.streak_days}</span>
          </div>
          <p className="text-xs text-fg-muted mt-0.5">天</p>
        </div>
        <div className="panel-card p-4 text-center">
          <p className="text-[10px] uppercase tracking-wider text-fg-dim mb-1">进度</p>
          <p className="text-2xl font-bold text-fg tabular">
            {data.chapters_completed}/{data.chapters_total}
          </p>
          <p className="text-xs text-fg-muted mt-0.5">章节</p>
        </div>
      </div>

      {/* XP progress bar */}
      <div className="panel-card p-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-fg font-medium">经验值进度</span>
          <span className="text-xs text-fg-muted tabular">
            {data.total_xp} / {data.next_level_xp} XP
          </span>
        </div>
        <div className="w-full bg-bg-subtle rounded-full h-3 overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${xpPct}%`, backgroundColor: levelColor }}
          />
        </div>
        <p className="text-xs text-fg-muted mt-2">
          再获得 {data.next_level_xp - data.total_xp} XP 即可升级
        </p>
      </div>

      {/* Tasks summary */}
      <div className="panel-card p-5">
        <div className="flex items-center gap-2 mb-3">
          <CheckCircle className="h-4 w-4 text-emerald-400" />
          <span className="text-sm text-fg font-medium">任务完成情况</span>
          <span className="text-xs text-fg-muted ml-auto tabular">
            {data.quests_completed}/{data.quests_total}
          </span>
        </div>
        <div className="w-full bg-bg-subtle rounded-full h-2.5 overflow-hidden">
          <div
            className="h-full rounded-full bg-emerald-400 transition-all duration-700"
            style={{ width: `${data.quests_total > 0 ? Math.round((data.quests_completed / data.quests_total) * 100) : 0}%` }}
          />
        </div>
      </div>

      {/* Chapters by category */}
      <div className="space-y-6">
        {grouped.map(({ category, chapters }) => (
          <div key={category}>
            <h2 className="text-xs uppercase tracking-[0.15em] text-fg-dim mb-4">{category} · {category === "基础" ? "建立认知" : category === "操作" ? "动手实践" : "融会贯通"}</h2>
            <div className="space-y-2">
              {chapters.map((ch) => {
                const questPct = ch.quests_total > 0 ? Math.round((ch.quests_done / ch.quests_total) * 100) : 0;
                return (
                  <button
                    key={ch.id}
                    onClick={() => navigate(`/learning/${ch.id}`)}
                    className="w-full panel-card p-4 flex items-center gap-4 text-left hover:bg-bg-hover transition-colors group"
                  >
                    {/* Chapter number badge */}
                    <div className={`shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                      ch.completed
                        ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-400"
                        : "bg-bg-subtle border border-line text-fg-muted"
                    }`}>
                      {ch.completed ? "✓" : ch.number}
                    </div>

                    {/* Title + progress bar */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-fg font-medium">{ch.title}</p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <div className="flex-1 bg-bg-subtle rounded-full h-1.5 overflow-hidden max-w-[160px]">
                          <div
                            className={`h-full rounded-full transition-all ${ch.completed ? "bg-emerald-400" : CATEGORY_COLORS[category] || "bg-fg-dim"}`}
                            style={{ width: `${ch.completed ? 100 : questPct}%` }}
                          />
                        </div>
                        <span className="text-[10px] text-fg-dim tabular">{ch.quests_done}/{ch.quests_total}</span>
                      </div>
                    </div>

                    <ChevronRight className="h-4 w-4 text-fg-dim opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
