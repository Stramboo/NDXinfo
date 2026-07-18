/**
 * MistakeBook.tsx — 错题本组件
 *
 * 通过 /api/mistakes 拉取错题列表，按 knowledge_point 分组展示，
 * 顶部显示总览统计与知识点分布条形图（纯 CSS div）。
 * 每条错题显示：来源 / 题目ID / 知识点 / 错误次数 / 掌握度（0/1/2 图标）。
 * "标记已复习"按钮：POST /api/mistakes/{source}/{question_id}/review
 */
import { useEffect, useState, useMemo } from "react";
import {
  CheckCircle2,
  Circle,
  AlertCircle,
  RotateCw,
  Brain,
} from "lucide-react";

// ---------- 类型定义 ----------

interface Mistake {
  source: string;          // 来源（如 stage_exam / scenario / lesson_quiz）
  question_id: string;     // 题目 ID
  knowledge_point: string; // 知识点
  wrong_count: number;     // 错误次数
  mastery: 0 | 1 | 2;      // 掌握度：0=未掌握 1=部分 2=已掌握
  last_wrong_at?: number;  // 最后一次错误时间
  reviewed?: boolean;      // 是否已复习
}

interface MistakeBookProps {
  /** 可选：自定义 API base，默认空走 Vite proxy */
  apiBase?: string;
}

// 掌握度图标
function MasteryIcon({ level }: { level: 0 | 1 | 2 }) {
  if (level === 0) return <AlertCircle className="w-4 h-4 text-rose-400" />;
  if (level === 1) return <Circle className="w-4 h-4 text-amber-400" />;
  return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
}

const MASTERY_LABEL: Record<number, string> = {
  0: "未掌握",
  1: "部分掌握",
  2: "已掌握",
};

const SOURCE_LABEL: Record<string, string> = {
  stage_exam: "阶段考试",
  scenario: "情景训练",
  lesson_quiz: "课时测验",
  emotion: "情绪训练",
  replay: "历史回放",
};

// ===================== 主组件 =====================

export function MistakeBook({ apiBase = "" }: MistakeBookProps) {
  const [mistakes, setMistakes] = useState<Mistake[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reviewing, setReviewing] = useState<string | null>(null);

  // 拉取错题列表
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`${apiBase}/api/mistakes`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        if (cancelled) return;
        // 兼容数组或 {mistakes: [...]} 两种返回格式
        const list: Mistake[] = Array.isArray(data)
          ? data
          : data?.mistakes ?? [];
        setMistakes(list);
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          const msg = e instanceof Error ? e.message : "加载失败";
          setError(msg);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [apiBase]);

  // 按 knowledge_point 分组
  const grouped = useMemo(() => {
    const map = new Map<string, Mistake[]>();
    for (const m of mistakes) {
      const key = m.knowledge_point || "未分类";
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(m);
    }
    // 每组内部按错误次数倒序
    for (const arr of map.values()) {
      arr.sort((a, b) => b.wrong_count - a.wrong_count);
    }
    // 组间按组内题目数倒序
    return Array.from(map.entries()).sort(
      (a, b) => b[1].length - a[1].length
    );
  }, [mistakes]);

  // 顶部统计
  const stats = useMemo(() => {
    const total = mistakes.length;
    const maxCount = Math.max(1, ...grouped.map(([, arr]) => arr.length));
    const totalWrong = mistakes.reduce((s, m) => s + m.wrong_count, 0);
    const mastered = mistakes.filter((m) => m.mastery >= 2).length;
    return { total, maxCount, totalWrong, mastered };
  }, [mistakes, grouped]);

  // 标记已复习
  const markReviewed = async (m: Mistake) => {
    const key = `${m.source}/${m.question_id}`;
    setReviewing(key);
    try {
      const res = await fetch(
        `${apiBase}/api/mistakes/${encodeURIComponent(m.source)}/${encodeURIComponent(
          m.question_id
        )}/review`,
        { method: "POST" }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      // 本地乐观更新
      setMistakes((prev) =>
        prev.map((x) =>
          x.source === m.source && x.question_id === m.question_id
            ? {
                ...x,
                reviewed: true,
                mastery: Math.max(1, x.mastery) as 0 | 1 | 2,
              }
            : x
        )
      );
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "标记失败";
      setError(msg);
    } finally {
      setReviewing(null);
    }
  };

  // ---------- 渲染 ----------

  if (loading) {
    return (
      <div className="glass-card p-6 space-y-3">
        <div className="h-5 w-32 rounded bg-white/[0.06] animate-pulse" />
        <div className="h-24 rounded-xl bg-white/[0.04] animate-pulse" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card p-6 text-center space-y-2">
        <AlertCircle className="w-6 h-6 text-rose-400 mx-auto" />
        <p className="text-sm text-fg-muted">加载错题失败</p>
        <p className="text-xs text-fg-dim">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* 顶部统计卡片 + 知识点分布条形图 */}
      <div className="glass-card specular-edge p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-fg">错题本</h3>
          </div>
          <span className="text-xs text-fg-dim">
            共 {stats.total} 题 · 累计错误 {stats.totalWrong} 次 · 已掌握 {stats.mastered}
          </span>
        </div>

        {/* 知识点分布条形图（纯 CSS div） */}
        {grouped.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-[10px] uppercase tracking-[0.15em] text-fg-dim">
              知识点分布
            </p>
            {grouped.map(([kp, arr]) => {
              const pct = (arr.length / stats.maxCount) * 100;
              return (
                <div key={kp} className="flex items-center gap-2 text-xs">
                  <span className="w-24 shrink-0 truncate text-fg-muted">{kp}</span>
                  <div className="flex-1 h-2 rounded-full bg-white/[0.04] overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-emerald-400/80 to-emerald-500 transition-all duration-300"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="w-8 text-right text-fg-dim tabular">
                    {arr.length}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 分组列表 */}
      {grouped.length === 0 ? (
        <div className="glass-card p-8 text-center space-y-2">
          <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
          <p className="text-sm text-fg">暂无错题记录</p>
          <p className="text-xs text-fg-dim">继续练习，错题会自动收录到这里</p>
        </div>
      ) : (
        <div className="space-y-4">
          {grouped.map(([kp, arr]) => (
            <div key={kp} className="glass-card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-fg">{kp}</h4>
                <span className="text-xs text-fg-dim">
                  {arr.length} 题 · 错误 {arr.reduce((s, m) => s + m.wrong_count, 0)} 次
                </span>
              </div>
              <div className="space-y-2">
                {arr.map((m) => {
                  const key = `${m.source}/${m.question_id}`;
                  return (
                    <div
                      key={key}
                      className="glass-light rounded-[12px] p-3 flex items-center gap-3"
                    >
                      <MasteryIcon level={m.mastery} />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-fg">
                          <span className="glass-pill px-1.5 py-0.5 rounded text-[10px] text-fg-muted mr-1">
                            {SOURCE_LABEL[m.source] || m.source}
                          </span>
                          <span className="text-fg-dim">#{m.question_id}</span>
                        </p>
                        <p className="text-[11px] text-fg-dim mt-0.5">
                          错误 {m.wrong_count} 次 · {MASTERY_LABEL[m.mastery]}
                          {m.reviewed && " · 已复习"}
                        </p>
                      </div>
                      <button
                        type="button"
                        disabled={m.reviewed || reviewing === key}
                        onClick={() => markReviewed(m)}
                        className="glass-btn px-3 py-1.5 rounded-[10px] text-xs text-fg disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
                      >
                        {reviewing === key ? (
                          <RotateCw className="w-3 h-3 animate-spin" />
                        ) : (
                          <CheckCircle2 className="w-3 h-3" />
                        )}
                        {m.reviewed ? "已复习" : "标记已复习"}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
