/**
 * Journal — 交易日志页面
 *
 * 功能：创建/编辑/删除交易日志，统计摘要面板，
 *       自动计算盈亏，评级和标签系统。
 */

import { useEffect, useState, useCallback } from "react";
import {
  Plus, Trash2, Star, TrendingUp, TrendingDown,
  Target, Award, BarChart3, Tag, DollarSign,
} from "lucide-react";
import { api, type JournalEntry, type JournalStats } from "../lib/api";
import { fmtMoney } from "../lib/utils";

// ---- 格式化 ----

const fmtNum = (v: number, frac = 2) =>
  v.toLocaleString("en-US", { minimumFractionDigits: frac, maximumFractionDigits: frac });

export function Journal() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [stats, setStats] = useState<JournalStats | null>(null);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 添加表单
  const [formSymbol, setFormSymbol] = useState("");
  const [formDir, setFormDir] = useState("long");
  const [formEntryDate, setFormEntryDate] = useState("");
  const [formExitDate, setFormExitDate] = useState("");
  const [formEntryPrice, setFormEntryPrice] = useState("");
  const [formExitPrice, setFormExitPrice] = useState("");
  const [formQty, setFormQty] = useState("");
  const [formRating, setFormRating] = useState(0);
  const [formTags, setFormTags] = useState("");
  const [formNotes, setFormNotes] = useState("");

  // ---- 数据加载 ----

  const load = useCallback(async () => {
    try {
      const [e, s] = await Promise.all([
        api.journal(),
        api.journalStats(),
      ]);
      setEntries(e);
      setStats(s);
      setError(null);
    } catch (err: any) {
      setError(err?.message || "加载失败");
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // ---- 自动计算盈亏 ----

  const computeAutoPnl = (): number | null => {
    const ep = Number(formEntryPrice);
    const xp = Number(formExitPrice);
    const q = Number(formQty);
    if (!ep || !xp || !q) return null;
    const raw = (xp - ep) * q;
    return formDir === "long" ? raw : -raw;
  };

  const autoPnl = computeAutoPnl();

  // ---- 操作 ----

  const resetForm = () => {
    setFormSymbol(""); setFormDir("long"); setFormEntryDate("");
    setFormExitDate(""); setFormEntryPrice(""); setFormExitPrice("");
    setFormQty(""); setFormRating(0); setFormTags(""); setFormNotes("");
    setAdding(false);
  };

  const doCreate = async () => {
    if (!formSymbol.trim() || !formEntryDate || !formEntryPrice || !formQty) return;

    const tagsArr = formTags
      .split(",")
      .map(t => t.trim())
      .filter(Boolean);

    try {
      await api.createJournalEntry({
        symbol: formSymbol.trim().toUpperCase(),
        direction: formDir,
        entry_date: formEntryDate,
        exit_date: formExitDate || undefined,
        entry_price: Number(formEntryPrice),
        exit_price: formExitPrice ? Number(formExitPrice) : undefined,
        quantity: Number(formQty),
        pnl: autoPnl ?? undefined,
        rating: formRating > 0 ? formRating : undefined,
        tags: tagsArr.length > 0 ? tagsArr : undefined,
        notes: formNotes.trim(),
      });
      resetForm();
      load();
    } catch (e: any) {
      setError(e?.message || "添加失败");
    }
  };

  const doDelete = async (id: number) => {
    if (!confirm("确定删除该日志？")) return;
    try {
      await api.deleteJournalEntry(id);
      load();
    } catch (e: any) {
      setError(e?.message || "删除失败");
    }
  };

  // ---- 评级星标 ----

  const StarRating = ({ value, onChange, readonly = false }: {
    value: number; onChange?: (v: number) => void; readonly?: boolean;
  }) => (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map(i => (
        <button
          key={i}
          disabled={readonly}
          type="button"
          onClick={() => onChange?.(i)}
          className={`transition ${readonly ? "cursor-default" : "cursor-pointer hover:scale-110"}`}
        >
          <Star
            className={`h-4 w-4 ${
              i <= value
                ? "fill-amber-400 text-amber-400"
                : "text-fg-dim"
            }`}
          />
        </button>
      ))}
    </div>
  );

  // ---- 渲染 ----

  const winRate = stats && stats.total_trades > 0
    ? stats.win_rate
    : 0;

  return (
    <div className="space-y-4 pb-8">
      {/* 错误提示 */}
      {error && (
        <div className="px-4 py-3 bg-neg text-rose-400 rounded-lg text-sm flex items-center gap-2">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-xs underline">关闭</button>
        </div>
      )}

      {/* 统计摘要 */}
      <div className="grid grid-cols-5 gap-4">
        <div className="panel-card p-5">
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 flex items-center gap-1.5">
            <BarChart3 className="h-3 w-3" /> 总交易
          </div>
          <div className="tabular text-2xl font-bold text-fg">
            {stats?.total_trades ?? "—"}
          </div>
        </div>
        <div className="panel-card p-5">
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 flex items-center gap-1.5">
            <Target className="h-3 w-3" /> 胜率
          </div>
          <div className={`tabular text-2xl font-bold ${winRate >= 50 ? "text-emerald-400" : "text-rose-400"}`}>
            {stats ? `${winRate.toFixed(1)}%` : "—"}
          </div>
          {stats && stats.total_trades > 0 && (
            <div className="text-[10px] text-fg-dim mt-1">
              {stats.profitable_count}盈 / {stats.unprofitable_count}亏
            </div>
          )}
        </div>
        <div className="panel-card p-5">
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 flex items-center gap-1.5">
            <TrendingUp className="h-3 w-3" /> 平均盈亏
          </div>
          <div className={`tabular text-2xl font-bold ${(stats?.avg_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
            {stats ? `${stats.avg_pnl >= 0 ? "+" : ""}$${fmtMoney(Math.abs(stats.avg_pnl))}` : "—"}
          </div>
        </div>
        <div className="panel-card p-5">
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 flex items-center gap-1.5">
            <Award className="h-3 w-3" /> 平均评级
          </div>
          <div className="tabular text-2xl font-bold text-fg flex items-center gap-1.5">
            {stats?.avg_rating ? (
              <>
                {stats.avg_rating.toFixed(1)}
                <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
              </>
            ) : "—"}
          </div>
        </div>
        <div className="panel-card p-5">
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 flex items-center gap-1.5">
            <DollarSign className="h-3 w-3" /> 累计盈亏
          </div>
          <div className={`tabular text-2xl font-bold ${(stats?.total_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
            {stats ? `${stats.total_pnl >= 0 ? "+" : ""}$${fmtMoney(Math.abs(stats.total_pnl))}` : "—"}
          </div>
        </div>
      </div>

      {/* 操作栏 */}
      <div className="flex items-center justify-between">
        <h2 className="text-fg text-lg font-semibold">交易记录</h2>
        <button
          onClick={() => setAdding(true)}
          className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 bg-bg-subtle px-3 py-1.5 rounded-lg transition"
        >
          <Plus className="h-3 w-3" /> 新建日志
        </button>
      </div>

      {/* 新建日志表单 */}
      {adding && (
        <div className="panel-card p-4 space-y-3">
          <div className="text-sm font-semibold text-fg">新建交易日志</div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 block">
                代码
              </label>
              <input
                autoFocus
                value={formSymbol}
                onChange={e => setFormSymbol(e.target.value)}
                placeholder="NVDA"
                className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-sm text-fg tabular focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 block">
                方向
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setFormDir("long")}
                  className={`flex-1 py-2 rounded-lg text-sm transition border ${
                    formDir === "long"
                      ? "bg-emerald-500/10 border-emerald-500 text-emerald-400"
                      : "bg-bg-subtle border-line text-fg-muted hover:bg-bg-hover"
                  }`}
                >
                  <TrendingUp className="h-3.5 w-3.5 inline mr-1" />
                  做多
                </button>
                <button
                  type="button"
                  onClick={() => setFormDir("short")}
                  className={`flex-1 py-2 rounded-lg text-sm transition border ${
                    formDir === "short"
                      ? "bg-rose-500/10 border-rose-500 text-rose-400"
                      : "bg-bg-subtle border-line text-fg-muted hover:bg-bg-hover"
                  }`}
                >
                  <TrendingDown className="h-3.5 w-3.5 inline mr-1" />
                  做空
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 block">
                入场日期
              </label>
              <input
                type="date"
                value={formEntryDate}
                onChange={e => setFormEntryDate(e.target.value)}
                className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-sm text-fg focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 block">
                出场日期
              </label>
              <input
                type="date"
                value={formExitDate}
                onChange={e => setFormExitDate(e.target.value)}
                className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-sm text-fg focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 block">
                入场价
              </label>
              <input
                type="number"
                step="any"
                value={formEntryPrice}
                onChange={e => setFormEntryPrice(e.target.value)}
                placeholder="0.00"
                className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-sm text-fg tabular focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 block">
                出场价
              </label>
              <input
                type="number"
                step="any"
                value={formExitPrice}
                onChange={e => setFormExitPrice(e.target.value)}
                placeholder="0.00"
                className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-sm text-fg tabular focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 block">
                数量
              </label>
              <input
                type="number"
                step="any"
                value={formQty}
                onChange={e => setFormQty(e.target.value)}
                placeholder="0"
                className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-sm text-fg tabular focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {/* 自动计算盈亏预览 */}
          {autoPnl !== null && (
            <div className={`px-3 py-2 rounded-lg text-sm ${
              autoPnl >= 0 ? "bg-pos text-emerald-400" : "bg-neg text-rose-400"
            }`}>
              预估盈亏：{autoPnl >= 0 ? "+" : ""}${fmtMoney(autoPnl)}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 block">
                评级 (1-5)
              </label>
              <StarRating value={formRating} onChange={setFormRating} />
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 block">
                标签 (逗号分隔)
              </label>
              <input
                value={formTags}
                onChange={e => setFormTags(e.target.value)}
                placeholder="swing, breakout, earnings"
                className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-sm text-fg focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div>
            <label className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 block">
              备注
            </label>
            <textarea
              value={formNotes}
              onChange={e => setFormNotes(e.target.value)}
              placeholder="交易复盘与心得..."
              rows={3}
              className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-sm text-fg focus:outline-none focus:border-emerald-500 resize-none"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={doCreate}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-emerald-500 text-bg hover:bg-emerald-600 transition"
            >
              保存
            </button>
            <button
              onClick={resetForm}
              className="px-4 py-2 rounded-lg text-sm text-fg-muted bg-bg-subtle hover:bg-bg-hover transition"
            >
              取消
            </button>
          </div>
        </div>
      )}

      {/* 日志列表 */}
      {entries.length === 0 ? (
        <div className="panel-card p-10 text-center text-fg-muted text-sm">
          暂无交易记录，点击"新建日志"记录你的第一笔交易。
        </div>
      ) : (
        <div className="space-y-2">
          {entries.map(entry => {
            const isLong = entry.direction === "long";
            const isProfit = (entry.pnl ?? 0) >= 0;

            return (
              <div
                key={entry.id}
                className="panel-card p-4 hover:bg-bg-hover/30 transition group"
              >
                <div className="flex items-start justify-between gap-4">
                  {/* 左侧信息 */}
                  <div className="flex-1 min-w-0 space-y-1.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-bold text-fg tabular">
                        {entry.symbol}
                      </span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-medium ${
                        isLong
                          ? "bg-emerald-500/10 text-emerald-400"
                          : "bg-rose-500/10 text-rose-400"
                      }`}>
                        {isLong ? "做多" : "做空"}
                      </span>
                      <span className="text-xs text-fg-muted">
                        {entry.entry_date}
                        {entry.exit_date && ` → ${entry.exit_date}`}
                      </span>
                      {entry.pnl !== null && (
                        <span className={`tabular text-sm font-semibold ${isProfit ? "text-emerald-400" : "text-rose-400"}`}>
                          {isProfit ? "+" : ""}${fmtMoney(Number(entry.pnl))}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-xs text-fg-muted">
                      <span className="tabular">
                        入场 ${fmtNum(entry.entry_price)}
                        {entry.exit_price ? ` → 出场 $${fmtNum(entry.exit_price)}` : ""}
                      </span>
                      <span className="tabular">数量 {fmtNum(entry.quantity, 0)}</span>
                    </div>

                    {entry.tags && entry.tags.length > 0 && (
                      <div className="flex items-center gap-1 flex-wrap">
                        <Tag className="h-3 w-3 text-fg-dim" />
                        {entry.tags.map((t, i) => (
                          <span
                            key={i}
                            className="text-[10px] px-1.5 py-0.5 rounded bg-bg-subtle text-fg-muted"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    )}

                    {entry.rating !== null && entry.rating > 0 && (
                      <StarRating value={entry.rating} readonly />
                    )}

                    {entry.notes && (
                      <p className="text-xs text-fg-muted leading-relaxed line-clamp-2">
                        {entry.notes}
                      </p>
                    )}
                  </div>

                  {/* 右侧操作 */}
                  <button
                    onClick={() => doDelete(entry.id)}
                    className="p-1.5 rounded text-fg-dim hover:text-rose-400 hover:bg-bg-hover opacity-0 group-hover:opacity-100 transition shrink-0"
                    title="删除"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}


