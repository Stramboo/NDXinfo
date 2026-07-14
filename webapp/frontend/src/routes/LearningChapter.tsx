/**
 * LearningChapter.tsx — 章节阅读页（左文右练）
 *
 * 从 /api/learning/chapters 获取全量数据，用 chapterId 匹配单章。
 * 底部自动检测滚动完成 → 标记进度。
 */

import { useEffect, useState, useRef, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Check } from "lucide-react";
import { KLineChart } from "../features/KLineChart";
import { SandboxTradePanel } from "../features/SandboxTradePanel";

type Section = { heading: string; paragraphs: string[] };
type Interactive = { type: string; instructions?: string } | null;

type ChapterData = {
  id: string; number: number; title: string; summary: string;
  category: string; sections: Section[]; interactive: Interactive; completed: boolean;
};

export function LearningChapter() {
  const { chapterId } = useParams<{ chapterId: string }>();
  const navigate = useNavigate();
  const [chapter, setChapter] = useState<ChapterData | null>(null);
  const [loading, setLoading] = useState(true);
  const [markedDone, setMarkedDone] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chapterId) return;
    let cancelled = false;
    setLoading(true);
    fetch("/api/learning/chapters")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (!cancelled && d?.chapters) {
          const found = d.chapters.find((c: ChapterData) => c.id === chapterId);
          setChapter(found || null);
          if (found?.completed) setMarkedDone(true);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [chapterId]);

  // Scroll-completion detection
  useEffect(() => {
    if (!scrollRef.current || !chapterId || markedDone) return;
    const el = scrollRef.current;
    const checkScroll = () => {
      const threshold = el.scrollHeight - el.clientHeight - 80;
      if (el.scrollTop >= threshold && !markedDone) {
        setMarkedDone(true);
        fetch(`/api/learning/progress`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ chapter_id: chapterId }),
        }).catch(() => {});
      }
    };
    el.addEventListener("scroll", checkScroll, { passive: true });
    return () => el.removeEventListener("scroll", checkScroll);
  }, [chapterId, markedDone]);

  const interactive = chapter?.interactive;

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-fg-muted text-sm">加载中...</div>;
  }

  if (!chapter) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <p className="text-fg-muted text-sm">章节未找到</p>
        <button onClick={() => navigate("/learning")} className="text-xs text-emerald-400 hover:text-emerald-300">
          返回学习路径
        </button>
      </div>
    );
  }

  return (
    <div className="flex gap-0 h-full" style={{ minHeight: "calc(100vh - 4rem - 2rem)" }}>
      {/* --- Left: Content --- */}
      <div ref={scrollRef} className="flex-1 overflow-auto pr-8">
        <button onClick={() => navigate("/learning")}
                className="inline-flex items-center gap-1.5 text-xs text-fg-muted hover:text-fg transition-colors mb-6">
          <ArrowLeft className="h-3.5 w-3.5" /> 学习路径
        </button>

        <div className="mb-2">
          <span className="text-xs uppercase tracking-wider text-fg-dim">
            第 {chapter.number} 章 · {chapter.category}
          </span>
        </div>
        <h1 className="text-2xl font-semibold text-fg tracking-tight mb-2">{chapter.title}</h1>
        <p className="text-sm text-fg-muted mb-8">{chapter.summary}</p>

        <div className="space-y-8 pb-20">
          {chapter.sections.map((sec, i) => (
            <div key={i}>
              <h2 className="text-base font-semibold text-fg mb-3">{sec.heading}</h2>
              {sec.paragraphs.map((p, j) => (
                <p key={j} className="text-sm text-fg-muted leading-relaxed mb-3">{p}</p>
              ))}
            </div>
          ))}

          {/* Completion marker */}
          <div className="pt-6 border-t border-line text-center">
            {markedDone ? (
              <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400">
                <Check className="h-3.5 w-3.5" /> 已完成
              </span>
            ) : (
              <span className="text-xs text-fg-dim">继续阅读以标记完成</span>
            )}
          </div>
        </div>
      </div>

      {/* --- Right: Interactive --- */}
      <div className="w-[420px] shrink-0 border-l border-line pl-8">
        <h3 className="text-xs uppercase tracking-[0.15em] text-fg-dim mb-4">互动练习</h3>

        <div className="panel-card p-5">
          {interactive?.instructions && (
            <p className="text-sm text-fg-muted mb-4">{interactive.instructions}</p>
          )}

          {interactive?.type === "sandbox_trade" && <SandboxTradePanel />}

          {interactive?.type === "chart_view" && (
            <div>
              <p className="text-sm text-fg-muted mb-3">观察下方图表，注意价格变化的趋势和关键点位。</p>
              <div className="h-80"><KLineChart symbol="NVDA" /></div>
            </div>
          )}

          {interactive?.type === "indicator_view" && (
            <div>
              <p className="text-sm text-fg-muted mb-3">技术指标叠加在 K 线图上，观察它们与价格的关系。</p>
              <div className="h-72"><KLineChart symbol="NVDA" /></div>
              <div className="mt-3 text-xs text-fg-dim leading-relaxed">
                上方是 K 线图和 MA 均线。该图表的副图区展示 MACD 和 RSI 指标。
                切换到交易页面可以看到完整的技术指标面板。
              </div>
            </div>
          )}

          {interactive?.type === "risk_scenario" && (
            <div className="space-y-3">
              <p className="text-sm text-fg-muted">
                假设你以 $100 买入 100 股 NVDA，共投入 $10,000。
              </p>
              <div className="bg-bg-subtle rounded-lg p-3 text-xs text-fg-muted space-y-1">
                <p>当前价格：<span className="text-rose-400 tabular font-semibold">$87</span></p>
                <p>浮亏：<span className="text-rose-400 tabular font-semibold">-$1,300 (13%)</span></p>
              </div>
              <p className="text-sm text-fg-muted">
                如果你在 $90 设了止损单，这笔亏损会被限制在 $1,000（10%），而不是 $1,300。
              </p>
              <p className="text-sm text-fg font-medium mt-2">关键教训</p>
              <ul className="text-xs text-fg-muted space-y-1 list-disc pl-4">
                <li>止损不是承认失败，是保护你自己</li>
                <li>没有止损的交易 = 赌博</li>
                <li>专业交易者把每笔最大亏损控制在 2-5%</li>
              </ul>
            </div>
          )}

          {interactive?.type === "portfolio_builder" && (
            <div className="space-y-3">
              <p className="text-sm text-fg-muted">
                一个好的投资组合不是一只股票涨多少，而是整体波动有多稳。
              </p>
              <div className="bg-bg-subtle rounded-lg p-3 text-xs text-fg-muted space-y-1.5">
                <p className="text-fg font-medium text-sm mb-1">示例组合（$100,000）</p>
                <div className="flex justify-between"><span>NVDA · 半导体</span><span className="tabular">20%</span></div>
                <div className="flex justify-between"><span>AAPL · 消费科技</span><span className="tabular">20%</span></div>
                <div className="flex justify-between"><span>MSFT · 企业软件</span><span className="tabular">20%</span></div>
                <div className="flex justify-between"><span>JNJ · 医药</span><span className="tabular">15%</span></div>
                <div className="flex justify-between"><span>现金储备</span><span className="tabular">25%</span></div>
              </div>
              <p className="text-xs text-fg-dim">
                注意：不要把超过 30% 的钱放在同一行业，永远留现金。
              </p>
            </div>
          )}

          {interactive?.type === "analysis_view" && (
            <div className="space-y-3">
              <p className="text-sm text-fg-muted">
                市场情绪通过多个维度衡量。以下是核心情绪指标：
              </p>
              <div className="bg-bg-subtle rounded-lg p-3 text-xs space-y-2">
                <div className="flex justify-between">
                  <span className="text-fg-muted">VIX（恐慌指数）</span>
                  <span className="text-fg tabular">18.5</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-fg-muted">状态</span>
                  <span className="text-emerald-400">正常范围（15-25）</span>
                </div>
                <div className="w-full bg-bg rounded-full h-1.5 mt-1 overflow-hidden">
                  <div className="h-full bg-amber-500 rounded-full" style={{ width: "35%" }} />
                </div>
              </div>
              <p className="text-xs text-fg-dim">
                VIX &lt; 15 = 平静 · 15-25 = 正常 · &gt; 30 = 恐慌。
                去分析页面查看实时的 NDX 大盘情绪数据。
              </p>
            </div>
          )}

          {!interactive && (
            <div className="text-sm text-fg-muted py-8 text-center">
              <p>此章节以阅读为主。</p>
              <p className="text-xs mt-2 text-fg-dim">完成阅读后继续下一章。</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
