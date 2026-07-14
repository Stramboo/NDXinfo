/**
 * Glossary.tsx --- Clean searchable glossary page.
 *
 * Search input at top. Category filter tabs below.
 * Results shown as simple term + definition cards.
 * Powered by /api/glossary and /api/glossary/search.
 */

import { useEffect, useState, useMemo, useCallback } from "react";
import { Search, BookOpen } from "lucide-react";

// ---- Types ----

type GlossaryEntry = {
  term: string;
  definition: string;
  category?: string;
};

// ---- Category config ----

const CATEGORIES = [
  { key: "全部", label: "全部" },
  { key: "基础", label: "基础" },
  { key: "技术分析", label: "技术分析" },
  { key: "交易操作", label: "交易操作" },
  { key: "组合管理", label: "组合管理" },
  { key: "风险管理", label: "风险管理" },
  { key: "市场情绪", label: "市场情绪" },
];

// ---- Cache helpers ----

const CACHE_KEY = "ndxinfo.glossary_cache";
const CACHE_TTL = 24 * 60 * 60 * 1000;

function loadGlossaryCache(): GlossaryEntry[] | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const { ts, entries } = JSON.parse(raw);
    if (Date.now() - ts > CACHE_TTL) {
      localStorage.removeItem(CACHE_KEY);
      return null;
    }
    return entries;
  } catch {
    return null;
  }
}

function saveGlossaryCache(entries: GlossaryEntry[]) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), entries }));
  } catch { /* ignore */ }
}

// ---- Component ----

export function Glossary() {
  const [entries, setEntries] = useState<GlossaryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("全部");

  // Load entries
  useEffect(() => {
    let cancelled = false;

    const cached = loadGlossaryCache();
    if (cached) {
      setEntries(cached);
      setLoading(false);
      return;
    }

    fetch("/api/glossary")
      .then((r) => (r.ok ? r.json() : []))
      .then((data: GlossaryEntry[]) => {
        if (!cancelled) {
          setEntries(data);
          saveGlossaryCache(data);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, []);

  // Search via API when query is entered
  useEffect(() => {
    if (!query.trim()) return;
    let cancelled = false;

    fetch(`/api/glossary/search?q=${encodeURIComponent(query)}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data: GlossaryEntry[] | null) => {
        if (!cancelled && data) setEntries(data);
      })
      .catch(() => {});

    return () => { cancelled = true; };
  }, [query]);

  // Client-side filter
  const filtered = useMemo(() => {
    let result = entries;

    // Category filter
    if (activeCategory !== "全部") {
      result = result.filter((e) => e.category === activeCategory);
    }

    // Client-side search (fallback if API search not used)
    if (query.trim()) {
      const q = query.toLowerCase();
      result = result.filter(
        (e) =>
          e.term.toLowerCase().includes(q) ||
          e.definition.toLowerCase().includes(q),
      );
    }

    return result;
  }, [entries, query, activeCategory]);

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div className="mb-2">
        <div className="flex items-center gap-3 mb-1">
          <BookOpen className="h-6 w-6 text-fg-muted" />
          <h1 className="text-2xl font-semibold text-fg tracking-tight">
            交易术语
          </h1>
        </div>
        <p className="text-sm text-fg-muted mt-1">
          搜索和浏览股票交易相关的专业术语解释。
        </p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-fg-dim" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="搜索术语..."
          className="w-full bg-bg-input border border-line rounded-xl pl-10 pr-4 py-3
                     text-sm text-fg placeholder:text-fg-dim
                     focus:outline-none focus:border-emerald-500 transition-colors"
        />
      </div>

      {/* Category tabs */}
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.key}
            onClick={() => setActiveCategory(cat.key)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
              activeCategory === cat.key
                ? "bg-emerald-500/10 border-emerald-500 text-emerald-400"
                : "bg-bg-subtle border-line text-fg-muted hover:bg-bg-hover hover:text-fg"
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && (
        <div className="text-center py-16 text-fg-muted text-sm">加载中...</div>
      )}

      {/* Results */}
      {!loading && (
        <div className="space-y-3">
          {filtered.length === 0 ? (
            <div className="text-center py-16 text-fg-muted text-sm">
              {query.trim()
                ? `未找到匹配 "${query}" 的术语`
                : "暂无术语数据"}
            </div>
          ) : (
            filtered.map((entry, i) => (
              <div
                key={`${entry.term}-${i}`}
                className="panel-card p-5"
              >
                <div className="flex items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5">
                      <h3 className="text-fg font-semibold text-sm">
                        {entry.term}
                      </h3>
                      {entry.category && (
                        <span className="text-[10px] uppercase tracking-wider text-fg-dim
                                         px-1.5 py-0.5 rounded bg-bg-subtle border border-line">
                          {entry.category}
                        </span>
                      )}
                    </div>
                    <p className="text-fg-muted text-sm leading-relaxed">
                      {entry.definition}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
