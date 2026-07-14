/**
 * AIAdvisor — AI 每日推荐页面
 *
 * 展示：
 * - 市场总览 + 一句话总结
 * - TOP 5 Picks 卡片
 * - 按操作建议分组（强烈买入/买入/持有/卖出）
 * - 每只股票评分条 + 理由
 * - 单股票详情展开
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Brain, Zap, TrendingUp, TrendingDown, Minus,
  ChevronDown, ChevronUp, Target, BarChart3, Shield,
  Loader2, RefreshCw,
} from "lucide-react";
import { fmtMoney } from "../lib/utils";

type Factor = { score: number; max: number; detail: string };
type StockRec = {
  symbol: string; name: string; sector: string;
  price: number; change_pct: number; score: number;
  action: string; action_label: string; reason: string;
  factors: Record<string, Factor>;
  rsi: number | null; macd_signal: string;
  support: number | null; resistance: number | null;
};

type RecData = {
  generated_at: string; total_stocks: number;
  market_summary: string;
  strong_buy: StockRec[]; buy: StockRec[];
  hold: StockRec[]; sell: StockRec[]; strong_sell: StockRec[];
  top_picks: StockRec[];
};

export function AIAdvisor() {
  const [data, setData] = useState<RecData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const navigate = useNavigate();

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/advisor/recommendations");
      if (!res.ok) throw new Error(await res.text());
      const d = await res.json();
      setData(d);
    } catch (e: any) {
      setError(e?.message || "加载失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const toggleExpand = (sym: string) => {
    setExpanded(prev => ({ ...prev, [sym]: !prev[sym] }));
  };

  const actionColor = (a: string) => {
    switch (a) {
      case "STRONG_BUY": return "bg-emerald-500 text-white";
      case "BUY": return "bg-emerald-500/20 text-emerald-400";
      case "HOLD": return "bg-amber-500/20 text-amber-400";
      case "SELL": return "bg-rose-500/20 text-rose-400";
      case "STRONG_SELL": return "bg-rose-500 text-white";
      default: return "bg-bg-subtle text-fg-muted";
    }
  };

  const scoreColor = (s: number) => {
    if (s >= 80) return "text-emerald-400";
    if (s >= 65) return "text-emerald-300";
    if (s >= 40) return "text-amber-400";
    return "text-rose-400";
  };

  const scoreBg = (s: number) => {
    if (s >= 80) return "bg-emerald-500";
    if (s >= 65) return "bg-emerald-400";
    if (s >= 40) return "bg-amber-500";
    return "bg-rose-500";
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-fg-muted">
        <Loader2 className="h-10 w-10 animate-spin mb-4 text-emerald-400" />
        <div className="text-lg font-medium">AI 正在分析 12 只股票…</div>
        <div className="text-sm mt-1">拉取实时数据 + 计算技术指标 + 多因子打分</div>
        <div className="text-xs text-fg-dim mt-3">预计需要 15-30 秒</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-32 text-fg-muted">
        <div className="text-rose-400 mb-2">加载失败</div>
        <div className="text-sm">{error}</div>
        <button onClick={fetchData} className="mt-4 px-4 py-2 bg-bg-subtle rounded-lg text-sm hover:bg-bg-hover">
          重试
        </button>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6 pb-8">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-fg flex items-center gap-2">
            <Brain className="h-6 w-6 text-violet-400" />
            AI 每日推荐
          </h1>
          <p className="text-xs text-fg-muted mt-1">
            {data.market_summary}
            <span className="ml-2 text-fg-dim">{data.generated_at}</span>
          </p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs bg-bg-subtle text-fg-muted hover:bg-bg-hover transition"
        >
          <RefreshCw className="h-3.5 w-3.5" /> 刷新
        </button>
      </div>

      {/* TOP 5 Picks */}
      <div>
        <h2 className="text-fg text-lg font-semibold mb-3 flex items-center gap-2">
          <Zap className="h-5 w-5 text-amber-400" /> 今日精选
        </h2>
        <div className="grid grid-cols-5 gap-3">
          {data.top_picks.map((r, i) => (
            <div
              key={r.symbol}
              onClick={() => navigate(`/trading?symbol=${r.symbol}`)}
              className="panel-card p-4 cursor-pointer hover:border-emerald-500/30 transition border border-line relative overflow-hidden group"
            >
              <div className="absolute -right-6 -top-4 text-6xl font-black text-fg/5 select-none group-hover:text-emerald-500/10 transition">
                {i + 1}
              </div>
              <div className="relative">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-bold text-fg tabular">{r.symbol}</span>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${actionColor(r.action)}`}>
                    {r.action_label}
                  </span>
                </div>
                <div className="tabular text-lg font-bold text-fg">${fmtMoney(r.price)}</div>
                <div className={`text-xs tabular mt-0.5 ${r.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {r.change_pct >= 0 ? "+" : ""}{r.change_pct.toFixed(2)}%
                </div>
                <div className="flex items-center gap-2 mt-3">
                  <div className="flex-1 h-1.5 bg-bg rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${scoreBg(r.score)}`}
                         style={{ width: `${r.score}%` }} />
                  </div>
                  <span className={`tabular text-xs font-bold ${scoreColor(r.score)}`}>{r.score}</span>
                </div>
                <div className="text-[10px] text-fg-muted mt-2 leading-relaxed">{r.reason}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 全部股票按分组 */}
      <TierSection
        title="强烈买入"
        icon={<TrendingUp className="h-5 w-5 text-emerald-400" />}
        color="border-emerald-500/30"
        stocks={data.strong_buy}
        actionColor={actionColor}
        scoreColor={scoreColor}
        scoreBg={scoreBg}
        expanded={expanded}
        toggleExpand={toggleExpand}
        onNavigate={(s) => navigate(`/trading?symbol=${s}`)}
      />
      <TierSection
        title="买入"
        icon={<TrendingUp className="h-5 w-5 text-emerald-300" />}
        color="border-emerald-500/20"
        stocks={data.buy}
        actionColor={actionColor}
        scoreColor={scoreColor}
        scoreBg={scoreBg}
        expanded={expanded}
        toggleExpand={toggleExpand}
        onNavigate={(s) => navigate(`/trading?symbol=${s}`)}
      />
      <TierSection
        title="持有观望"
        icon={<Minus className="h-5 w-5 text-amber-400" />}
        color="border-amber-500/20"
        stocks={data.hold}
        actionColor={actionColor}
        scoreColor={scoreColor}
        scoreBg={scoreBg}
        expanded={expanded}
        toggleExpand={toggleExpand}
        onNavigate={(s) => navigate(`/trading?symbol=${s}`)}
      />
      {data.sell.length > 0 && (
        <TierSection
          title="卖出"
          icon={<TrendingDown className="h-5 w-5 text-rose-400" />}
          color="border-rose-500/20"
          stocks={data.sell}
          actionColor={actionColor}
          scoreColor={scoreColor}
          scoreBg={scoreBg}
          expanded={expanded}
          toggleExpand={toggleExpand}
          onNavigate={(s) => navigate(`/trading?symbol=${s}`)}
        />
      )}
    </div>
  );
}

function TierSection({
  title, icon, color, stocks, actionColor, scoreColor, scoreBg,
  expanded, toggleExpand, onNavigate,
}: {
  title: string; icon: React.ReactNode; color: string;
  stocks: StockRec[];
  actionColor: (a: string) => string;
  scoreColor: (s: number) => string;
  scoreBg: (s: number) => string;
  expanded: Record<string, boolean>;
  toggleExpand: (s: string) => void;
  onNavigate: (s: string) => void;
}) {
  if (stocks.length === 0) return null;

  return (
    <div>
      <h2 className="text-fg text-lg font-semibold mb-3 flex items-center gap-2">{icon} {title}</h2>
      <div className="space-y-2">
        {stocks.map(r => {
          const open = expanded[r.symbol] || false;
          return (
            <div
              key={r.symbol}
              className={`panel-card overflow-hidden border transition ${open ? color : "border-line"}`}
            >
              <div
                onClick={() => toggleExpand(r.symbol)}
                className="flex items-center gap-4 px-5 py-3 cursor-pointer hover:bg-bg-hover/30 transition"
              >
                {/* 评分 */}
                <div className="w-12 text-center shrink-0">
                  <div className={`tabular text-lg font-bold ${scoreColor(r.score)}`}>{r.score}</div>
                  <div className="w-full h-1 bg-bg rounded-full mt-0.5 overflow-hidden">
                    <div className={`h-full rounded-full ${scoreBg(r.score)}`}
                         style={{ width: `${r.score}%` }} />
                  </div>
                </div>

                {/* 基本信息 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-fg">{r.symbol}</span>
                    <span className="text-xs text-fg-muted">{r.name}</span>
                    <span className="text-[10px] text-fg-dim bg-bg-subtle px-1.5 py-0.5 rounded">{r.sector}</span>
                  </div>
                  <div className="text-xs text-fg-muted mt-0.5">{r.reason}</div>
                </div>

                {/* 价格 */}
                <div className="text-right shrink-0">
                  <div className="tabular text-sm font-semibold text-fg">${fmtMoney(r.price)}</div>
                  <div className={`tabular text-xs ${r.change_pct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    {r.change_pct >= 0 ? "+" : ""}{r.change_pct.toFixed(2)}%
                  </div>
                </div>

                {/* 操作标签 */}
                <span className={`px-2 py-1 rounded text-[10px] font-bold shrink-0 ${actionColor(r.action)}`}>
                  {r.action_label}
                </span>

                {open ? <ChevronUp className="h-4 w-4 text-fg-muted" /> : <ChevronDown className="h-4 w-4 text-fg-muted" />}
              </div>

              {/* 展开详情 */}
              {open && (
                <div className="px-5 pb-4 pt-0 space-y-3 border-t border-line/50 mt-0">
                  {/* 因子条 */}
                  <div className="grid grid-cols-5 gap-3">
                    {r.factors && Object.entries(r.factors).map(([k, f]) => (
                      <div key={k} className="bg-bg-subtle rounded-lg p-2.5">
                        <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1">
                          {k === "trend" ? "趋势" : k === "momentum" ? "动量" : k === "reversal" ? "反转" : k === "volume" ? "量价" : "波动"}
                        </div>
                        <div className="tabular text-sm font-bold text-fg">
                          {f.score.toFixed(1)}
                          <span className="text-fg-dim text-xs">/{f.max}</span>
                        </div>
                        <div className="w-full h-1 bg-bg rounded-full mt-1 overflow-hidden">
                          <div className={`h-full rounded-full ${f.score / f.max >= 0.7 ? "bg-emerald-500" : f.score / f.max >= 0.4 ? "bg-amber-500" : "bg-rose-500"}`}
                               style={{ width: `${(f.score / f.max) * 100}%` }} />
                        </div>
                        <div className="text-[10px] text-fg-dim mt-1 leading-tight">{f.detail}</div>
                      </div>
                    ))}
                  </div>

                  {/* 额外信息 */}
                  <div className="flex items-center gap-4 text-xs text-fg-muted">
                    {r.rsi != null && <span>RSI: <span className="tabular text-fg">{r.rsi.toFixed(1)}</span></span>}
                    <span>MACD: <span className={r.macd_signal === "bull" ? "text-emerald-400" : "text-rose-400"}>{r.macd_signal === "bull" ? "多头" : "空头"}</span></span>
                    {r.support && <span>支撑: <span className="tabular text-fg">${fmtMoney(r.support)}</span></span>}
                    {r.resistance && <span>压力: <span className="tabular text-fg">${fmtMoney(r.resistance)}</span></span>}
                  </div>

                  <button
                    onClick={(e) => { e.stopPropagation(); onNavigate(r.symbol); }}
                    className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
                  >
                    <Target className="h-3 w-3" /> 去交易页面操作这只股票
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
