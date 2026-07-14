/**
 * Portfolio — 持仓组合管理页面
 *
 * 功能：添加/编辑/删除持仓，实时报价，盈亏计算，
 *       快照记录组合净值，净值曲线可视化。
 */

import { useEffect, useState, useCallback } from "react";
import {
  Plus, Trash2, Camera, TrendingUp, TrendingDown,
  DollarSign, PieChart, Briefcase,
} from "lucide-react";
import { api, type PortfolioHolding, type PortfolioSnapshot } from "../lib/api";
import { fmtMoney, fmtPct } from "../lib/utils";

// ---- 格式化工具 ----

const fmtNum = (v: number, frac = 2) =>
  v.toLocaleString("en-US", { minimumFractionDigits: frac, maximumFractionDigits: frac });

// ---- 报价缓存 ----

type QuoteMap = Record<string, { price: number; ts: number }>;

export function Portfolio() {
  const [holdings, setHoldings] = useState<PortfolioHolding[]>([]);
  const [snapshots, setSnapshots] = useState<PortfolioSnapshot[]>([]);
  const [quotes, setQuotes] = useState<QuoteMap>({});
  const [adding, setAdding] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 添加表单
  const [formSymbol, setFormSymbol] = useState("");
  const [formName, setFormName] = useState("");
  const [formQty, setFormQty] = useState("");
  const [formCost, setFormCost] = useState("");
  const [formNotes, setFormNotes] = useState("");

  // 编辑表单
  const [editSymbol, setEditSymbol] = useState("");
  const [editName, setEditName] = useState("");
  const [editQty, setEditQty] = useState("");
  const [editCost, setEditCost] = useState("");
  const [editNotes, setEditNotes] = useState("");

  // ---- 数据加载 ----

  const load = useCallback(async () => {
    try {
      const [h, s] = await Promise.all([
        api.portfolio(),
        api.portfolioSnapshots(),
      ]);
      setHoldings(h);
      setSnapshots(s);
      setError(null);
    } catch (e: any) {
      setError(e?.message || "加载失败");
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // ---- 轮询报价 ----

  useEffect(() => {
    if (holdings.length === 0) return;
    let cancel = false;
    const fetchQuotes = async () => {
      const map: QuoteMap = {};
      for (const h of holdings) {
        try {
          const q = await api.quote(h.symbol);
          if (!cancel) map[h.symbol] = q;
        } catch { /* ignore */ }
      }
      if (!cancel) setQuotes(map);
    };
    fetchQuotes();
    const t = setInterval(fetchQuotes, 5000);
    return () => { cancel = true; clearInterval(t); };
  }, [holdings.map(h => h.symbol).join(",")]);

  // ---- 计算 ----

  const computePnL = (h: PortfolioHolding) => {
    const q = quotes[h.symbol];
    const price = q ? q.price : h.avg_cost;
    const mv = h.quantity * price;
    const cost = h.quantity * h.avg_cost;
    const pnl = mv - cost;
    const pnlPct = cost === 0 ? 0 : (pnl / cost) * 100;
    return { price, mv, pnl, pnlPct };
  };

  const totalMV = holdings.reduce((sum, h) => sum + computePnL(h).mv, 0);
  const totalCost = holdings.reduce((sum, h) => sum + h.quantity * h.avg_cost, 0);
  const totalPnl = totalMV - totalCost;
  const totalPnlPct = totalCost === 0 ? 0 : (totalPnl / totalCost) * 100;

  // ---- 操作 ----

  const resetAddForm = () => {
    setFormSymbol(""); setFormName(""); setFormQty("");
    setFormCost(""); setFormNotes(""); setAdding(false);
  };

  const doCreate = async () => {
    if (!formSymbol.trim() || !formName.trim() || !formQty || !formCost) return;
    try {
      await api.createHolding({
        symbol: formSymbol.trim().toUpperCase(),
        name: formName.trim(),
        quantity: Number(formQty),
        avg_cost: Number(formCost),
        notes: formNotes.trim(),
      });
      resetAddForm();
      load();
    } catch (e: any) {
      setError(e?.message || "添加失败");
    }
  };

  const startEdit = (h: PortfolioHolding) => {
    setEditingId(h.id);
    setEditSymbol(h.symbol);
    setEditName(h.name);
    setEditQty(String(h.quantity));
    setEditCost(String(h.avg_cost));
    setEditNotes(h.notes || "");
  };

  const cancelEdit = () => setEditingId(null);

  const doSaveEdit = async (id: number) => {
    if (!editSymbol.trim() || !editName.trim() || !editQty || !editCost) return;
    try {
      await api.updateHolding(id, {
        symbol: editSymbol.trim().toUpperCase(),
        name: editName.trim(),
        quantity: Number(editQty),
        avg_cost: Number(editCost),
        notes: editNotes.trim(),
      });
      setEditingId(null);
      load();
    } catch (e: any) {
      setError(e?.message || "保存失败");
    }
  };

  const doDelete = async (id: number) => {
    if (!confirm("确定删除该持仓？")) return;
    try {
      await api.deleteHolding(id);
      load();
    } catch (e: any) {
      setError(e?.message || "删除失败");
    }
  };

  const doSnapshot = async () => {
    try {
      await api.createPortfolioSnapshot({ total_value: totalMV });
      load();
    } catch (e: any) {
      setError(e?.message || "快照失败");
    }
  };

  // ---- 净值曲线数据 ----

  const chartData = snapshots.length >= 2
    ? snapshots.map(s => ({ ts: new Date(s.recorded_at).getTime(), value: s.total_value }))
    : [];

  const positive = totalPnl >= 0;

  return (
    <div className="space-y-4 pb-8">
      {/* 错误提示 */}
      {error && (
        <div className="px-4 py-3 bg-neg text-rose-400 rounded-lg text-sm flex items-center gap-2">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="ml-auto text-xs underline">关闭</button>
        </div>
      )}

      {/* 总览卡片 */}
      <div className="grid grid-cols-4 gap-4">
        <div className="panel-card p-5">
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 flex items-center gap-1.5">
            <DollarSign className="h-3 w-3" /> 组合总值
          </div>
          <div className="tabular text-2xl font-bold text-fg">
            ${fmtMoney(totalMV)}
          </div>
        </div>
        <div className="panel-card p-5">
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 flex items-center gap-1.5">
            {positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            未实现盈亏
          </div>
          <div className={`tabular text-2xl font-bold ${positive ? "text-emerald-400" : "text-rose-400"}`}>
            {positive ? "+" : ""}{fmtMoney(totalPnl)}
          </div>
          <div className={`tabular text-sm mt-1 ${positive ? "text-emerald-400/80" : "text-rose-400/80"}`}>
            {positive ? "▲" : "▼"} {fmtPct(totalPnlPct)}
          </div>
        </div>
        <div className="panel-card p-5">
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 flex items-center gap-1.5">
            <Briefcase className="h-3 w-3" /> 持仓数量
          </div>
          <div className="tabular text-2xl font-bold text-fg">
            {holdings.length}
          </div>
        </div>
        <div className="panel-card p-5">
          <div className="text-[10px] uppercase tracking-wider text-fg-muted mb-1 flex items-center gap-1.5">
            <PieChart className="h-3 w-3" /> 总成本
          </div>
          <div className="tabular text-2xl font-bold text-fg">
            ${fmtMoney(totalCost)}
          </div>
        </div>
      </div>

      {/* 净值曲线 */}
      {chartData.length >= 2 && (
        <PortfolioCurve snapshots={snapshots} />
      )}

      {/* 操作栏 */}
      <div className="flex items-center justify-between">
        <h2 className="text-fg text-lg font-semibold">持仓明细</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={doSnapshot}
            disabled={holdings.length === 0}
            className="flex items-center gap-1.5 text-xs text-fg-muted bg-bg-subtle hover:bg-bg-hover px-3 py-1.5 rounded-lg transition disabled:opacity-40"
            title="记录当前净值快照"
          >
            <Camera className="h-3.5 w-3.5" /> 快照
          </button>
          <button
            onClick={() => setAdding(true)}
            className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 bg-bg-subtle px-3 py-1.5 rounded-lg transition"
          >
            <Plus className="h-3 w-3" /> 添加持仓
          </button>
        </div>
      </div>

      {/* 添加持仓表单 */}
      {adding && (
        <div className="panel-card p-4 space-y-3">
          <div className="text-sm font-semibold text-fg">新增持仓</div>
          <div className="grid grid-cols-5 gap-3">
            <input
              autoFocus
              value={formSymbol}
              onChange={e => setFormSymbol(e.target.value)}
              placeholder="代码"
              className="bg-bg-input border border-line rounded-lg px-3 py-2 text-sm text-fg tabular focus:outline-none focus:border-emerald-500"
            />
            <input
              value={formName}
              onChange={e => setFormName(e.target.value)}
              placeholder="名称"
              className="bg-bg-input border border-line rounded-lg px-3 py-2 text-sm text-fg focus:outline-none focus:border-emerald-500"
            />
            <input
              value={formQty}
              onChange={e => setFormQty(e.target.value)}
              placeholder="数量"
              type="number"
              step="any"
              className="bg-bg-input border border-line rounded-lg px-3 py-2 text-sm text-fg tabular focus:outline-none focus:border-emerald-500"
            />
            <input
              value={formCost}
              onChange={e => setFormCost(e.target.value)}
              placeholder="均价"
              type="number"
              step="any"
              className="bg-bg-input border border-line rounded-lg px-3 py-2 text-sm text-fg tabular focus:outline-none focus:border-emerald-500"
            />
            <input
              value={formNotes}
              onChange={e => setFormNotes(e.target.value)}
              placeholder="备注"
              className="bg-bg-input border border-line rounded-lg px-3 py-2 text-sm text-fg focus:outline-none focus:border-emerald-500"
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
              onClick={resetAddForm}
              className="px-4 py-2 rounded-lg text-sm text-fg-muted bg-bg-subtle hover:bg-bg-hover transition"
            >
              取消
            </button>
          </div>
        </div>
      )}

      {/* 持仓列表 */}
      {holdings.length === 0 ? (
        <div className="panel-card p-10 text-center text-fg-muted text-sm">
          暂无持仓，点击"添加持仓"开始管理投资组合。
        </div>
      ) : (
        <div className="panel-card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-[10px] uppercase tracking-wider text-fg-muted">
                  <th className="text-left px-5 py-3 font-medium">代码</th>
                  <th className="text-left px-5 py-3 font-medium">名称</th>
                  <th className="text-right px-5 py-3 font-medium">数量</th>
                  <th className="text-right px-5 py-3 font-medium">均价</th>
                  <th className="text-right px-5 py-3 font-medium">现价</th>
                  <th className="text-right px-5 py-3 font-medium">市值</th>
                  <th className="text-right px-5 py-3 font-medium">未实现盈亏</th>
                  <th className="text-right px-5 py-3 font-medium">盈亏%</th>
                  <th className="text-center px-5 py-3 font-medium w-20">操作</th>
                </tr>
              </thead>
              <tbody>
                {holdings.map(h => {
                  const { price, mv, pnl, pnlPct } = computePnL(h);
                  const isPos = pnl >= 0;
                  const isEditing = editingId === h.id;

                  if (isEditing) {
                    return (
                      <tr key={h.id} className="border-b border-line/40 bg-bg-subtle/50">
                        <td className="px-5 py-2.5">
                          <input
                            value={editSymbol}
                            onChange={e => setEditSymbol(e.target.value)}
                            className="w-20 bg-bg-input border border-line rounded px-2 py-1 text-sm text-fg tabular focus:outline-none focus:border-emerald-500"
                          />
                        </td>
                        <td className="px-5 py-2.5">
                          <input
                            value={editName}
                            onChange={e => setEditName(e.target.value)}
                            className="w-28 bg-bg-input border border-line rounded px-2 py-1 text-sm text-fg focus:outline-none focus:border-emerald-500"
                          />
                        </td>
                        <td className="px-5 py-2.5 text-right">
                          <input
                            value={editQty}
                            onChange={e => setEditQty(e.target.value)}
                            type="number"
                            step="any"
                            className="w-20 bg-bg-input border border-line rounded px-2 py-1 text-sm text-fg tabular text-right focus:outline-none focus:border-emerald-500"
                          />
                        </td>
                        <td className="px-5 py-2.5 text-right">
                          <input
                            value={editCost}
                            onChange={e => setEditCost(e.target.value)}
                            type="number"
                            step="any"
                            className="w-20 bg-bg-input border border-line rounded px-2 py-1 text-sm text-fg tabular text-right focus:outline-none focus:border-emerald-500"
                          />
                        </td>
                        <td className="px-5 py-2.5 text-right tabular text-fg-muted">
                          ${fmtNum(price)}
                        </td>
                        <td className="px-5 py-2.5 text-right tabular text-fg-muted">
                          ${fmtMoney(mv)}
                        </td>
                        <td className="px-5 py-2.5" colSpan={2}>
                          <div className="flex items-center gap-2 justify-end">
                            <button
                              onClick={() => doSaveEdit(h.id)}
                              className="text-xs text-emerald-400 hover:text-emerald-300 px-2 py-1 rounded bg-emerald-500/10"
                            >
                              保存
                            </button>
                            <button
                              onClick={cancelEdit}
                              className="text-xs text-fg-muted hover:text-fg px-2 py-1 rounded bg-bg-hover"
                            >
                              取消
                            </button>
                          </div>
                        </td>
                        <td className="px-5 py-2.5 text-center">
                          <button
                            onClick={() => doDelete(h.id)}
                            className="p-1 rounded text-fg-dim hover:text-rose-400 hover:bg-bg-hover transition"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </td>
                      </tr>
                    );
                  }

                  return (
                    <tr
                      key={h.id}
                      className="border-b border-line/40 hover:bg-bg-hover/50 transition group"
                    >
                      <td className="px-5 py-3 font-semibold text-fg tabular">
                        {h.symbol}
                      </td>
                      <td className="px-5 py-3 text-fg-muted">
                        {h.name}
                        {h.notes && (
                          <span className="ml-2 text-[11px] text-fg-dim">— {h.notes}</span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-right tabular text-fg">
                        {fmtNum(h.quantity, 0)}
                      </td>
                      <td className="px-5 py-3 text-right tabular text-fg">
                        ${fmtNum(h.avg_cost)}
                      </td>
                      <td className="px-5 py-3 text-right tabular text-fg">
                        ${fmtNum(price)}
                      </td>
                      <td className="px-5 py-3 text-right tabular text-fg font-medium">
                        ${fmtMoney(mv)}
                      </td>
                      <td className={`px-5 py-3 text-right tabular font-medium ${isPos ? "text-emerald-400" : "text-rose-400"}`}>
                        {isPos ? "+" : ""}{fmtMoney(pnl)}
                      </td>
                      <td className={`px-5 py-3 text-right tabular ${isPos ? "text-emerald-400" : "text-rose-400"}`}>
                        {fmtPct(pnlPct)}
                      </td>
                      <td className="px-5 py-3 text-center">
                        <div className="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition">
                          <button
                            onClick={() => startEdit(h)}
                            className="p-1 rounded text-fg-dim hover:text-fg hover:bg-bg-hover transition"
                            title="编辑"
                          >
                            <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                            </svg>
                          </button>
                          <button
                            onClick={() => doDelete(h.id)}
                            className="p-1 rounded text-fg-dim hover:text-rose-400 hover:bg-bg-hover transition"
                            title="删除"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 快照历史 */}
      {snapshots.length > 0 && (
        <div className="panel-card p-5">
          <h2 className="text-fg text-lg font-semibold mb-4">净值快照历史</h2>
          <div className="grid grid-cols-6 gap-3">
            {[...snapshots].reverse().slice(0, 12).map(s => (
              <div key={s.id} className="bg-bg-subtle rounded-lg p-3 text-center">
                <div className="text-[10px] text-fg-muted uppercase tracking-wider">
                  {new Date(s.recorded_at).toLocaleDateString("zh-CN")}
                </div>
                <div className="text-xs text-fg-dim mt-0.5">
                  {new Date(s.recorded_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
                </div>
                <div className="tabular text-lg font-bold text-fg mt-1">
                  ${fmtMoney(s.total_value)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---- 净值曲线组件（纯 SVG）----

function PortfolioCurve({ snapshots }: { snapshots: PortfolioSnapshot[] }) {
  const data = snapshots.map(s => ({
    ts: new Date(s.recorded_at).getTime(),
    value: s.total_value,
  }));

  if (data.length < 2) return null;

  const W = 1000;
  const H = 220;
  const PAD = 32;

  const xs = data.map(d => d.ts);
  const ys = data.map(d => d.value);
  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  const yMin = Math.min(...ys);
  const yMax = Math.max(...ys);
  const yRange = Math.max(1, yMax - yMin);

  const toX = (x: number) => PAD + ((x - xMin) / (xMax - xMin || 1)) * (W - 2 * PAD);
  const toY = (y: number) => H - PAD - ((y - yMin) / yRange) * (H - 2 * PAD);

  const pts = data.map(d => [toX(d.ts), toY(d.value)] as [number, number]);

  let pathD = `M ${pts[0][0]} ${pts[0][1]}`;
  for (let i = 1; i < pts.length; i++) {
    const prev = pts[i - 1];
    const curr = pts[i];
    pathD += ` C ${prev[0] + (curr[0] - prev[0]) / 2} ${prev[1]}, ${prev[0] + (curr[0] - prev[0]) / 2} ${curr[1]}, ${curr[0]} ${curr[1]}`;
  }

  const areaD =
    pathD +
    ` L ${pts[pts.length - 1][0]} ${H - PAD} L ${pts[0][0]} ${H - PAD} Z`;

  const first = data[0].value;
  const last = data[data.length - 1].value;
  const diff = last - first;
  const diffPct = first === 0 ? 0 : (last / first - 1) * 100;
  const positive = diff >= 0;
  const stroke = positive ? "#10B981" : "#F43F5E";
  const fill = positive ? "url(#pf-pos)" : "url(#pf-neg)";

  return (
    <div className="panel-card p-5">
      <div className="flex items-end justify-between mb-3">
        <div>
          <div className="text-fg text-lg font-semibold">净值曲线</div>
          <div className={`tabular text-sm mt-1 ${positive ? "text-emerald-400" : "text-rose-400"}`}>
            {positive ? "▲" : "▼"} ${fmtMoney(Math.abs(diff))} ({fmtPct(diffPct)})
          </div>
        </div>
        <div className="text-xs text-fg-muted tabular">
          {snapshots.length} 个快照
        </div>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-56" preserveAspectRatio="none">
        <defs>
          <linearGradient id="pf-pos" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10B981" stopOpacity="0.32" />
            <stop offset="100%" stopColor="#10B981" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="pf-neg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#F43F5E" stopOpacity="0.32" />
            <stop offset="100%" stopColor="#F43F5E" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0.25, 0.5, 0.75].map(p => (
          <line key={p} x1={PAD} x2={W - PAD} y1={H * p} y2={H * p}
                stroke="#1F222C" strokeDasharray="2 4" />
        ))}
        <path d={areaD} fill={fill} />
        <path d={pathD} fill="none" stroke={stroke} strokeWidth={2} />
        <circle cx={pts[pts.length - 1][0]} cy={pts[pts.length - 1][1]} r="3" fill={stroke} />
      </svg>
    </div>
  );
}
