/**
 * HistoricalReplay.tsx — 历史事件回放页面
 *
 * 列表 + 详情双视图：
 *   - 列表：fetch /api/historical-events，显示事件卡片
 *           （标题 + 副标题 + 严重度 + 日期范围 + XP）
 *   - 详情：fetch /api/historical-events/:id
 *           时间轴展示 key_dates（竖向时间线）
 *           逐个决策点答题
 *   - 提交：fetch /api/historical-events/:id/submit
 *   - 结果页：评分 + 每个决策的历史结果对比 + 教训列表
 */
import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  History,
  Calendar,
  BookOpen,
} from "lucide-react";

// ---------- 类型定义 ----------

type Severity = "low" | "medium" | "high" | "extreme";

interface HistoricalEventSummary {
  id: string;
  title: string;
  subtitle: string;
  severity: Severity;
  start_date: string;
  end_date?: string;
  xp: number;
}

interface KeyEventDate {
  date: string;
  label: string;
  description?: string;
}

interface DecisionOption {
  id: string;
  text: string;
}

interface DecisionPoint {
  id: string;
  question: string;
  context?: string;
  options: DecisionOption[];
  historical_choice: string;        // 历史上真实选择
  historical_result: string;        // 历史结果描述
  evaluation?: {                    // 每个选项的评估
    [optionId: string]: {
      result: "good" | "partial" | "bad";
      feedback: string;
    };
  };
}

interface HistoricalEventDetail extends HistoricalEventSummary {
  description: string;
  key_dates: KeyEventDate[];
  decisions: DecisionPoint[];
  lessons?: string[];
}

interface ReplayComparison {
  question: string;
  your_choice: string;
  historical_choice: string;
  historical_result: string;
  your_result: "good" | "partial" | "bad";
  feedback: string;
}

interface ReplayResult {
  score: number;
  level: string;
  xp_earned: number;
  comparisons: ReplayComparison[];
  lessons: string[];
}

const SEVERITY_LABEL: Record<Severity, string> = {
  low: "低",
  medium: "中",
  high: "高",
  extreme: "极端",
};

const SEVERITY_COLOR: Record<Severity, string> = {
  low: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10",
  medium: "text-amber-400 border-amber-500/30 bg-amber-500/10",
  high: "text-orange-400 border-orange-500/30 bg-orange-500/10",
  extreme: "text-rose-400 border-rose-500/30 bg-rose-500/10",
};

// ===================== 主组件（列表） =====================

export function HistoricalReplay() {
  const [events, setEvents] = useState<HistoricalEventSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch("/api/historical-events")
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        if (cancelled) return;
        const list: HistoricalEventSummary[] = Array.isArray(data)
          ? data
          : data?.events ?? [];
        setEvents(list);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // 进入详情
  if (selectedId) {
    return (
      <EventDetail eventId={selectedId} onBack={() => setSelectedId(null)} />
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-6">
      {/* 面包屑 */}
      <div className="flex items-center gap-2 text-xs text-fg-dim">
        <Link to="/practice" className="hover:text-fg transition">
          练习
        </Link>
        <span>/</span>
        <span className="text-fg">历史回放</span>
      </div>

      <header className="space-y-1">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-emerald-400" />
          <h1 className="text-xl font-bold text-fg">历史事件回放</h1>
        </div>
        <p className="text-sm text-fg-muted">
          重历市场重大事件，对比你的决策与历史走向。
        </p>
      </header>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="glass-card h-28 animate-pulse" />
          ))}
        </div>
      ) : events.length === 0 ? (
        <div className="glass-card p-8 text-center space-y-2">
          <History className="w-8 h-8 text-fg-dim mx-auto" />
          <p className="text-sm text-fg-muted">暂无历史事件</p>
        </div>
      ) : (
        <div className="space-y-3">
          {events.map((ev) => (
            <button
              key={ev.id}
              onClick={() => setSelectedId(ev.id)}
              className="glass-card specular-edge w-full p-4 text-left hover:border-emerald-500/40 transition"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0 space-y-1">
                  <p className="text-sm font-semibold text-fg">{ev.title}</p>
                  <p className="text-xs text-fg-muted">{ev.subtitle}</p>
                  <div className="flex items-center gap-2 text-[10px] text-fg-dim mt-1.5">
                    <Calendar className="w-3 h-3" />
                    <span>
                      {ev.start_date}
                      {ev.end_date ? ` — ${ev.end_date}` : ""}
                    </span>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1.5 shrink-0">
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] border ${
                      SEVERITY_COLOR[ev.severity] || SEVERITY_COLOR.medium
                    }`}
                  >
                    {SEVERITY_LABEL[ev.severity] || ev.severity}
                  </span>
                  <span className="text-xs text-amber-400">+{ev.xp} XP</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ===================== 详情组件 =====================

function EventDetail({
  eventId,
  onBack,
}: {
  eventId: string;
  onBack: () => void;
}) {
  const [event, setEvent] = useState<HistoricalEventDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [decisions, setDecisions] = useState<Record<string, string>>({});
  const [currentDecision, setCurrentDecision] = useState(0);
  const [result, setResult] = useState<ReplayResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 拉取事件详情
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`/api/historical-events/${eventId}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (cancelled) return;
        setEvent(d);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [eventId]);

  // 选择某个决策点的选项（自动进入下一题）
  const handleChoose = useCallback(
    (decisionId: string, optionId: string) => {
      setDecisions((prev) => ({ ...prev, [decisionId]: optionId }));
      if (event) {
        const idx = event.decisions.findIndex((d) => d.id === decisionId);
        if (idx >= 0 && idx + 1 < event.decisions.length) {
          // 短暂延迟以提供视觉反馈
          setTimeout(() => setCurrentDecision(idx + 1), 250);
        }
      }
    },
    [event]
  );

  // 提交所有决策
  const handleSubmit = useCallback(async () => {
    if (!event) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`/api/historical-events/${eventId}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          decisions: event.decisions.map((d) => ({
            decision_id: d.id,
            choice: decisions[d.id] || "",
          })),
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult(data as ReplayResult);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "提交失败";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  }, [event, decisions, eventId]);

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 space-y-4">
        <div className="h-6 w-32 rounded bg-bg-subtle animate-pulse" />
        <div className="h-64 rounded-xl bg-bg-panel animate-pulse" />
      </div>
    );
  }

  if (!event) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 text-center space-y-2">
        <p className="text-sm text-fg-dim">事件未找到</p>
        <button
          onClick={onBack}
          className="text-xs text-emerald-400 hover:underline"
        >
          ← 返回列表
        </button>
      </div>
    );
  }

  // ---------- 结果页 ----------
  if (result) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
        <button
          onClick={onBack}
          className="text-xs text-fg-dim hover:text-fg transition flex items-center gap-1.5"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> 返回列表
        </button>

        <div className="text-center space-y-3">
          <div className="text-5xl">
            {result.score >= 80 ? "🏆" : result.score >= 50 ? "📚" : "💡"}
          </div>
          <h1 className="text-xl font-bold text-fg">
            {event.title} — 回放完成
          </h1>
          <p className="text-lg text-fg-muted">
            得分 <span className="text-emerald-400 font-bold">{result.score}</span>{" "}
            分 · {result.level}
          </p>
          {result.xp_earned > 0 && (
            <p className="text-xs text-amber-400">+{result.xp_earned} XP</p>
          )}
        </div>

        {/* 决策对比 */}
        <div className="space-y-3">
          <p className="text-xs text-fg-muted uppercase tracking-wider">
            决策对比
          </p>
          {result.comparisons.map((c, i) => (
            <div key={i} className="glass-card p-4 space-y-2">
              <p className="text-sm text-fg font-medium">{c.question}</p>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div
                  className={`glass-light rounded-[10px] p-2.5 ${
                    c.your_result === "good"
                      ? "border border-emerald-500/30"
                      : c.your_result === "bad"
                      ? "border border-rose-500/30"
                      : "border border-amber-500/30"
                  }`}
                >
                  <p className="text-fg-dim mb-0.5">你的选择</p>
                  <p className="text-fg">{c.your_choice}</p>
                </div>
                <div className="glass-light rounded-[10px] p-2.5">
                  <p className="text-fg-dim mb-0.5">历史选择</p>
                  <p className="text-fg">{c.historical_choice}</p>
                </div>
              </div>
              <div className="text-xs text-fg-muted leading-relaxed">
                <span className="text-fg-dim">历史结果：</span>
                {c.historical_result}
              </div>
              <div
                className={`text-xs leading-relaxed px-2 py-1.5 rounded ${
                  c.your_result === "good"
                    ? "text-emerald-400 bg-emerald-500/5"
                    : c.your_result === "bad"
                    ? "text-rose-400 bg-rose-500/5"
                    : "text-amber-400 bg-amber-500/5"
                }`}
              >
                {c.feedback}
              </div>
            </div>
          ))}
        </div>

        {/* 教训列表 */}
        {result.lessons && result.lessons.length > 0 && (
          <div className="glass-card specular-edge p-5 space-y-2">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-emerald-400" />
              <p className="text-xs text-fg-muted uppercase tracking-wider">
                教训
              </p>
            </div>
            {result.lessons.map((l, i) => (
              <p key={i} className="text-xs text-fg-muted leading-relaxed">
                • {l}
              </p>
            ))}
          </div>
        )}

        <div className="flex gap-3 justify-center">
          <button
            onClick={onBack}
            className="glass-btn px-4 py-2 rounded-[12px] text-sm text-fg"
          >
            返回列表
          </button>
          <button
            onClick={() => {
              setDecisions({});
              setCurrentDecision(0);
              setResult(null);
            }}
            className="glass-btn-primary px-4 py-2 rounded-[12px] text-sm font-semibold"
          >
            重新回放
          </button>
        </div>
      </div>
    );
  }

  // ---------- 决策答题页 ----------
  const total = event.decisions.length;
  const answered = event.decisions.filter((d) => decisions[d.id]).length;
  const allAnswered = total > 0 && answered === total;
  const current = event.decisions[currentDecision];

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
      <button
        onClick={onBack}
        className="text-xs text-fg-dim hover:text-fg transition flex items-center gap-1.5"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> 返回列表
      </button>

      {/* 头部 */}
      <header className="space-y-2">
        <div className="flex items-center gap-2">
          <span
            className={`px-2 py-0.5 rounded-full text-[10px] border ${
              SEVERITY_COLOR[event.severity] || SEVERITY_COLOR.medium
            }`}
          >
            严重度：{SEVERITY_LABEL[event.severity] || event.severity}
          </span>
          <span className="text-xs text-amber-400">+{event.xp} XP</span>
        </div>
        <h1 className="text-xl font-bold text-fg">{event.title}</h1>
        <p className="text-xs text-fg-muted">{event.subtitle}</p>
        <p className="text-sm text-fg-muted leading-relaxed">
          {event.description}
        </p>
      </header>

      {/* 时间轴（竖向） */}
      {event.key_dates && event.key_dates.length > 0 && (
        <div className="glass-card p-5 space-y-3">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-emerald-400" />
            <p className="text-xs text-fg-muted uppercase tracking-wider">
              关键时间线
            </p>
          </div>
          <div className="relative pl-4 space-y-3">
            {/* 竖线 */}
            <div className="absolute left-[5px] top-1 bottom-1 w-px bg-emerald-500/30" />
            {event.key_dates.map((d, i) => (
              <div key={i} className="relative">
                <span className="absolute -left-4 top-1 w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-bg" />
                <p className="text-xs font-semibold text-fg">{d.date}</p>
                <p className="text-sm text-fg mt-0.5">{d.label}</p>
                {d.description && (
                  <p className="text-xs text-fg-dim mt-0.5">{d.description}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 决策进度 */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1.5 rounded-full bg-bg-subtle overflow-hidden">
          <div
            className="h-full bg-emerald-500 rounded-full transition-all duration-300"
            style={{ width: `${(answered / Math.max(1, total)) * 100}%` }}
          />
        </div>
        <span className="text-xs text-fg-dim tabular">
          {answered}/{total}
        </span>
      </div>

      {/* 决策卡片 */}
      {current && (
        <div className="glass-card specular-edge p-6 space-y-4">
          <p className="text-xs text-fg-dim">
            决策点 {currentDecision + 1}
          </p>
          {current.context && (
            <div className="glass-light rounded-[12px] p-3 text-xs text-fg-muted">
              {current.context}
            </div>
          )}
          <p className="text-sm font-medium text-fg leading-relaxed">
            {current.question}
          </p>

          <div className="space-y-2">
            {current.options.map((opt) => {
              const isSelected = decisions[current.id] === opt.id;
              return (
                <button
                  key={opt.id}
                  onClick={() => handleChoose(current.id, opt.id)}
                  className={`w-full text-left p-3 rounded-[12px] border text-sm transition-all ${
                    isSelected
                      ? "border-emerald-500 bg-emerald-500/10 text-fg"
                      : "border-line glass-light text-fg-muted hover:border-emerald-500/30 hover:text-fg"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="w-5 text-center text-xs font-mono text-fg-dim">
                      {opt.id.toUpperCase()}
                    </span>
                    <span>{opt.text}</span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* 决策切换 */}
          <div className="flex items-center justify-between gap-2 pt-2">
            <button
              onClick={() => setCurrentDecision(Math.max(0, currentDecision - 1))}
              disabled={currentDecision === 0}
              className="glass-btn px-3 py-1.5 rounded-[10px] text-xs text-fg disabled:opacity-30"
            >
              ← 上一题
            </button>
            <button
              onClick={() =>
                setCurrentDecision(Math.min(total - 1, currentDecision + 1))
              }
              disabled={currentDecision === total - 1}
              className="glass-btn px-3 py-1.5 rounded-[10px] text-xs text-fg disabled:opacity-30"
            >
              下一题 →
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="glass-card p-3 text-xs text-rose-400 border border-rose-500/30">
          {error}
        </div>
      )}

      {/* 提交按钮 */}
      <button
        onClick={handleSubmit}
        disabled={!allAnswered || submitting}
        className="glass-btn-primary w-full py-2.5 rounded-[12px] text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {submitting
          ? "评估中..."
          : allAnswered
          ? "提交回放"
          : `还需回答 ${total - answered} 题`}
      </button>
    </div>
  );
}
