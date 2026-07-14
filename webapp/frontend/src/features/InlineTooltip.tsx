/**
 * InlineTooltip.tsx --- <Term> component with on-hover glossary lookup.
 *
 * Fetches glossary data from /api/glossary on first use and caches
 * in localStorage. On hover, looks up the term and shows a tooltip.
 * If the term is not found, renders children as plain text.
 */

import { useState, useRef, useCallback, type ReactNode } from "react";

// ---- Types ----

type GlossaryEntry = {
  term: string;
  definition: string;
  category?: string;
};

type GlossaryCache = {
  ts: number;
  entries: GlossaryEntry[];
};

// ---- Cache helpers ----

const CACHE_KEY = "ndxinfo.glossary_cache";
const CACHE_TTL = 24 * 60 * 60 * 1000; // 24 hours

function loadCache(): GlossaryCache | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const cache: GlossaryCache = JSON.parse(raw);
    if (Date.now() - cache.ts > CACHE_TTL) {
      localStorage.removeItem(CACHE_KEY);
      return null;
    }
    return cache;
  } catch {
    return null;
  }
}

function saveCache(entries: GlossaryEntry[]) {
  try {
    localStorage.setItem(
      CACHE_KEY,
      JSON.stringify({ ts: Date.now(), entries }),
    );
  } catch { /* quota exceeded — ignore */ }
}

// ---- Lazy loader ----

let _loadPromise: Promise<GlossaryEntry[]> | null = null;

function loadGlossary(): Promise<GlossaryEntry[]> {
  if (_loadPromise) return _loadPromise;

  const cached = loadCache();
  if (cached && cached.entries.length > 0) {
    _loadPromise = Promise.resolve(cached.entries);
    return _loadPromise;
  }

  _loadPromise = fetch("/api/glossary")
    .then((res) => {
      if (!res.ok) throw new Error("glossary fetch failed");
      return res.json();
    })
    .then((data: GlossaryEntry[]) => {
      saveCache(data);
      return data;
    })
    .catch(() => [] as GlossaryEntry[]);

  return _loadPromise;
}

// ---- Props ----

type TermProps = {
  term: string;
  children?: ReactNode;
};

// ---- Component ----

export function Term({ term, children }: TermProps) {
  const [def, setDef] = useState<string | null>(null);
  const [visible, setVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleEnter = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    // If we already have the definition, show immediately
    if (def !== null) {
      setVisible(true);
      return;
    }

    setLoading(true);
    timeoutRef.current = setTimeout(async () => {
      try {
        const entries = await loadGlossary();
        const entry = entries.find(
          (e) => e.term.toLowerCase() === term.toLowerCase(),
        );
        setDef(entry?.definition ?? "");
        setLoading(false);
        setVisible(true);
      } catch {
        setDef("");
        setLoading(false);
      }
    }, 200);
  }, [term, def]);

  const handleLeave = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setVisible(false);
  }, []);

  // No definition available (term not found in glossary)
  const hasDef = def !== null && def.length > 0;

  return (
    <span
      className="relative inline"
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
    >
      <span
        className={
          hasDef
            ? "border-b border-dashed border-fg-dim cursor-help"
            : ""
        }
      >
        {children ?? term}
      </span>

      {visible && (
        <div
          className="absolute z-40 bottom-full left-1/2 -translate-x-1/2 mb-2 pointer-events-none"
          style={{ maxWidth: 320 }}
        >
          <div
            className="px-4 py-3 rounded-lg text-sm leading-relaxed
                       bg-bg-panel border border-line shadow-lg
                       text-fg-muted whitespace-normal"
            style={{ minWidth: 200 }}
          >
            {loading ? (
              <span className="italic text-fg-dim">加载中...</span>
            ) : hasDef ? (
              <>
                <div className="text-xs uppercase tracking-wider text-fg mb-1">
                  {term}
                </div>
                {def}
              </>
            ) : null}
          </div>
        </div>
      )}
    </span>
  );
}
