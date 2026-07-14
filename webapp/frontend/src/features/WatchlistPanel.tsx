/**
 * WatchlistPanel — 自定义自选列表面板
 *
 * 功能：查看/切换/创建/编辑/删除自选列表，每行显示实时价格
 */

import { useEffect, useState } from "react";
import {
  Plus, Trash2, Edit3, Star, Check, X, RefreshCw, List,
} from "lucide-react";
import { api, type Watchlist, type PriceAlert } from "../lib/api";
import { AlertModal } from "./AlertModal";
import { useNavigate } from "react-router-dom";

const fmt = (v: number, frac = 2) =>
  v.toLocaleString("en-US", { minimumFractionDigits: frac, maximumFractionDigits: frac });
const pct = (v: number) => `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;

type QuoteMap = Record<string, { price: number; ts: number }>;

export function WatchlistPanel() {
  const [lists, setLists] = useState<Watchlist[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [quotes, setQuotes] = useState<QuoteMap>({});
  const [editing, setEditing] = useState<{ id: number; name: string; syms: string } | null>(null);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [alertTarget, setAlertTarget] = useState<string | null>(null);
  const navigate = useNavigate();

  // 加载自选列表
  const load = async () => {
    try {
      const data = await api.watchlists();
      setLists(data);
      if (!activeId && data.length > 0) setActiveId(data[0].id);
      else if (activeId && !data.find(l => l.id === activeId)) setActiveId(data[0]?.id ?? null);
    } catch { /* ignore */ }
  };

  useEffect(() => { load(); }, []);

  // 轮询实时报价
  const activeList = lists.find(l => l.id === activeId);
  useEffect(() => {
    if (!activeList) return;
    let cancel = false;
    const fetchQuotes = async () => {
      const map: QuoteMap = {};
      for (const sym of activeList.symbols) {
        try {
          const q = await api.quote(sym);
          if (!cancel) map[sym] = q;
        } catch { /* ignore */ }
      }
      if (!cancel) setQuotes(map);
    };
    fetchQuotes();
    const t = setInterval(fetchQuotes, 3000);
    return () => { cancel = true; clearInterval(t); };
  }, [activeList?.symbols.join(",")]);

  // 创建
  const doCreate = async () => {
    if (!newName.trim()) return;
    await api.createWatchlist({ name: newName.trim(), symbols: [] });
    setNewName("");
    setCreating(false);
    load();
  };

  // 保存编辑
  const saveEdit = async () => {
    if (!editing) return;
    const syms = editing.syms.split(",").map(s => s.trim().toUpperCase()).filter(Boolean);
    await api.updateWatchlist(editing.id, { name: editing.name, symbols: syms });
    setEditing(null);
    load();
  };

  // 删除
  const doDelete = async (id: number) => {
    if (!confirm("确定删除这个自选列表？")) return;
    await api.deleteWatchlist(id);
    load();
  };

  const symbols = activeList?.symbols || [];

  return (
    <div className="panel-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="flex items-center gap-2 text-fg text-lg font-semibold">
          <Star className="h-5 w-5 text-amber-400" />
          自选列表
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => load()}
            className="p-1.5 rounded text-fg-muted hover:text-fg hover:bg-bg-hover transition"
            title="刷新"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
          <button
            onClick={() => setCreating(true)}
            className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 bg-bg-subtle px-2 py-1.5 rounded transition"
          >
            <Plus className="h-3 w-3" /> 新建
          </button>
        </div>
      </div>

      {/* 列表选择 tabs */}
      {lists.length > 0 && (
        <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
          {lists.map(l => (
            <button
              key={l.id}
              onClick={() => setActiveId(l.id)}
              className={`px-3 py-1.5 rounded-lg text-xs whitespace-nowrap transition border ${
                l.id === activeId
                  ? "bg-emerald-500/10 border-emerald-500 text-emerald-400"
                  : "bg-bg-subtle border-line text-fg-muted hover:bg-bg-hover"
              }`}
            >
              {l.name} ({l.symbols.length})
            </button>
          ))}
        </div>
      )}

      {/* 创建弹窗 */}
      {creating && (
        <div className="mb-4 p-3 bg-bg-subtle rounded-lg flex items-center gap-2">
          <input
            autoFocus
            value={newName}
            onChange={e => setNewName(e.target.value)}
            onKeyDown={e => e.key === "Enter" && doCreate()}
            placeholder="列表名称"
            className="flex-1 bg-bg-input border border-line rounded px-2 py-1 text-xs text-fg focus:outline-none focus:border-emerald-500"
          />
          <button onClick={doCreate} className="p-1 text-emerald-400 hover:text-emerald-300"><Check className="h-4 w-4" /></button>
          <button onClick={() => setCreating(false)} className="p-1 text-fg-muted hover:text-fg"><X className="h-4 w-4" /></button>
        </div>
      )}

      {/* 编辑弹窗 */}
      {editing && (
        <div className="mb-4 p-3 bg-bg-subtle rounded-lg space-y-2">
          <input
            value={editing.name}
            onChange={e => setEditing({ ...editing, name: e.target.value })}
            className="w-full bg-bg-input border border-line rounded px-2 py-1 text-xs text-fg focus:outline-none focus:border-emerald-500"
            placeholder="名称"
          />
          <input
            value={editing.syms}
            onChange={e => setEditing({ ...editing, syms: e.target.value })}
            className="w-full bg-bg-input border border-line rounded px-2 py-1 text-xs text-fg focus:outline-none focus:border-emerald-500"
            placeholder="标的（逗号分隔）如 NVDA,AAPL,TSLA"
          />
          <div className="flex gap-2">
            <button onClick={saveEdit} className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1">
              <Check className="h-3 w-3" /> 保存
            </button>
            <button onClick={() => setEditing(null)} className="text-xs text-fg-muted hover:text-fg flex items-center gap-1">
              <X className="h-3 w-3" /> 取消
            </button>
          </div>
        </div>
      )}

      {/* 股票列表 */}
      {symbols.length === 0 ? (
        <div className="text-center py-6 text-fg-muted text-sm">
          {activeList ? (
            <div className="space-y-2">
              <List className="h-6 w-6 mx-auto text-fg-dim" />
              <p>列表为空</p>
              <button
                onClick={() => setEditing({
                  id: activeList.id,
                  name: activeList.name,
                  syms: activeList.symbols.join(", "),
                })}
                className="text-xs text-emerald-400 hover:text-emerald-300"
              >
                点击添加标的
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <p>还没有自选列表</p>
              <button onClick={() => setCreating(true)} className="text-xs text-emerald-400 hover:text-emerald-300">
                新建一个
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-1">
          {symbols.map(sym => {
            const q = quotes[sym];
            return (
              <div key={sym}
                   className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-bg-hover transition cursor-pointer group"
                   onClick={() => navigate(`/trading?symbol=${sym}`)}>
                <span className="text-sm font-semibold text-fg tabular">{sym}</span>
                <div className="flex items-center gap-3">
                  {q ? (
                    <span className="tabular text-sm text-fg">
                      ${fmt(q.price, 2)}
                    </span>
                  ) : (
                    <span className="text-xs text-fg-muted">加载中</span>
                  )}
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition">
                    <button
                      onClick={e => { e.stopPropagation(); setAlertTarget(sym); }}
                      className="p-0.5 rounded text-amber-400 hover:bg-amber-400/10"
                      title="设告警"
                    >
                      <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
          {/* 编辑/删除按钮 */}
          <div className="flex items-center gap-2 pt-2 mt-2 border-t border-line">
            <button
              onClick={() => activeList && setEditing({
                id: activeList.id,
                name: activeList.name,
                syms: activeList.symbols.join(", "),
              })}
              className="flex items-center gap-1 text-[10px] text-fg-muted hover:text-fg transition"
            >
              <Edit3 className="h-3 w-3" /> 编辑
            </button>
            <button
              onClick={() => activeList && doDelete(activeList.id)}
              className="flex items-center gap-1 text-[10px] text-rose-400 hover:text-rose-300 transition"
            >
              <Trash2 className="h-3 w-3" /> 删除
            </button>
          </div>
        </div>
      )}

      {/* 告警弹窗 */}
      {alertTarget && (
        <AlertModal
          symbol={alertTarget}
          onClose={() => setAlertTarget(null)}
          onCreated={() => { setAlertTarget(null); }}
        />
      )}
    </div>
  );
}
