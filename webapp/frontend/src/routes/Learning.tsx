/**
 * Learning.tsx --- 学习路径主页（8 章列表，3 个分类）
 *
 * 数据来源：/api/learning/chapters → { chapters: [{..., completed: bool}] }
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BookOpen, ChevronRight, GraduationCap } from "lucide-react";

type ChapterSummary = {
  id: string;
  number: number;
  title: string;
  summary: string;
  category: string;
  completed: boolean;
};

export function Learning() {
  const [chapters, setChapters] = useState<ChapterSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    fetch("/api/learning/chapters")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!cancelled && d?.chapters) setChapters(d.chapters);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const CATEGORY_LABELS: Record<string, string> = {
    "基础": "基础概念",
    "操作": "操作实践",
    "进阶": "进阶分析",
  };
  const CATEGORY_ORDER = ["基础", "操作", "进阶"];

  const grouped = CATEGORY_ORDER.reduce(
    (acc, cat) => {
      const items = chapters.filter((ch) => ch.category === cat);
      if (items.length > 0) acc.push({ category: cat, items });
      return acc;
    },
    [] as { category: string; items: ChapterSummary[] }[],
  );

  return (
    <div className="max-w-5xl mx-auto space-y-10 pb-16">
      {/* Header */}
      <div className="mb-2">
        <div className="flex items-center gap-3 mb-1">
          <GraduationCap className="h-6 w-6 text-fg-muted" />
          <h1 className="text-2xl font-semibold text-fg tracking-tight">
            学习路径
          </h1>
        </div>
        <p className="text-sm text-fg-muted mt-1">
          从零开始，逐步掌握股票交易的核心知识与操作技能。
        </p>
      </div>

      {loading && (
        <div className="text-center py-16 text-fg-muted text-sm">加载中...</div>
      )}

      {/* Category groups */}
      <div className="space-y-12">
        {grouped.length === 0 && !loading && (
          <div className="text-center py-16 text-fg-muted text-sm">
            暂无课程数据。请确认后端服务已启动。
          </div>
        )}

        {grouped.map(({ category, items }) => (
          <section key={category}>
            <h2 className="text-xs uppercase tracking-[0.15em] text-fg-dim mb-5">
              {CATEGORY_LABELS[category] ?? category}
            </h2>

            <div className="space-y-1">
              {items.map((ch) => (
                <button
                  key={ch.id}
                  onClick={() => navigate(`/learning/${ch.id}`)}
                  className="w-full flex items-center gap-5 px-4 py-4 rounded-lg
                             text-left transition-colors
                             hover:bg-bg-hover group"
                >
                  <div className="relative shrink-0">
                    <span className="block w-9 h-9 rounded-full
                                     border border-line bg-bg-subtle
                                     text-xs font-semibold tabular
                                     text-fg-muted grid place-items-center
                                     group-hover:border-fg-dim transition-colors">
                      {ch.number}
                    </span>
                    <span className={`absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border transition-colors ${
                      ch.completed
                        ? "bg-emerald-500 border-emerald-500"
                        : "bg-transparent border-line"
                    }`} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <h3 className="text-fg text-sm font-medium">{ch.title}</h3>
                    <p className="text-fg-muted text-xs mt-0.5 leading-relaxed line-clamp-2">
                      {ch.summary}
                    </p>
                  </div>

                  <ChevronRight className="h-4 w-4 text-fg-dim shrink-0
                                            opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
