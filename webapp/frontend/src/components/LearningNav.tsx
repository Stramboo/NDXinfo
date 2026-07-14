/**
 * LearningNav.tsx --- Small expandable component for the bottom of the Sidebar.
 *
 * Shows a "学习" link that expands into a chapter list on click.
 * Each chapter shows a small circle (filled if completed).
 * Uses learning progress from the API, cached locally.
 */

import { useState, useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { GraduationCap, ChevronRight } from "lucide-react";
import { cn } from "../lib/utils";

// ---- Types ----

type ChapterMeta = {
  id: string;
  number: number;
  title: string;
};

type ProgressData = {
  chapters: ChapterMeta[];
  completed: string[];
};

// ---- Component ----

export function LearningNav() {
  const [expanded, setExpanded] = useState(false);
  const [data, setData] = useState<ProgressData | null>(null);
  const location = useLocation();

  // Load progress on mount
  useEffect(() => {
    fetch("/api/learning/chapters")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d) {
          setData({
            chapters: d.chapters ?? [],
            completed: d.completed ?? [],
          });
        }
      })
      .catch(() => {});
  }, []);

  // Auto-expand when on a learning route
  useEffect(() => {
    if (location.pathname.startsWith("/learning")) {
      setExpanded(true);
    }
  }, [location.pathname]);

  const chapters = data?.chapters ?? [];
  const completed = data?.completed ?? [];

  return (
    <div className="border-t border-line pt-2">
      {/* Toggle button */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className={cn(
          "flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm transition",
          "hover:bg-bg-hover",
          location.pathname.startsWith("/learning")
            ? "bg-bg-hover text-fg shadow-[inset_2px_0_0_0_#10B981]"
            : "text-fg-muted",
        )}
      >
        <GraduationCap className="h-4 w-4" />
        <span className="flex-1 text-left">学习</span>
        <ChevronRight
          className={cn(
            "h-3.5 w-3.5 transition-transform",
            expanded && "rotate-90",
          )}
        />
      </button>

      {/* Chapter list */}
      {expanded && (
        <div className="mt-1 ml-9 space-y-0.5 pr-2 pb-2">
          {chapters.length === 0 && (
            <p className="text-[11px] text-fg-dim px-1 py-2">暂无章节</p>
          )}
          {chapters.slice(0, 8).map((ch) => {
            const isDone = completed.includes(ch.id);
            return (
              <NavLink
                key={ch.id}
                to={`/learning/${ch.id}`}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-2 px-2 py-1.5 rounded text-xs transition-colors",
                    "hover:bg-bg-hover",
                    isActive
                      ? "text-fg bg-bg-hover"
                      : "text-fg-muted",
                  )
                }
              >
                {/* Circle indicator */}
                <span
                  className={cn(
                    "w-2 h-2 rounded-full shrink-0 border transition-colors",
                    isDone
                      ? "bg-emerald-500 border-emerald-500"
                      : "border-fg-dim",
                  )}
                />
                <span className="truncate">
                  {ch.number}. {ch.title}
                </span>
              </NavLink>
            );
          })}
        </div>
      )}
    </div>
  );
}
