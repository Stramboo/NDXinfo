/**
 * KnowledgeMap.tsx — 知识点图谱
 *
 * 通过 /api/knowledge-map 拉取知识点节点，按 stage 分组（6 个阶段）展示。
 * 每个知识点节点：圆点（按掌握度着色）+ 名称。
 *   - 绿 = 100       已掌握
 *   - 黄 = 50-99     部分掌握
 *   - 红 = <50       未掌握
 * 顶部展示图例说明。
 */
import { useEffect, useState, useMemo } from "react";
import { Brain, Circle } from "lucide-react";

// ---------- 类型定义 ----------

interface KnowledgeNode {
  id: string;
  name: string;
  stage: number;        // 1-6
  mastery: number;      // 0-100
  description?: string;
  prerequisites?: string[];
}

interface KnowledgeMapProps {
  apiBase?: string;
}

// 按掌握度返回颜色（绿 / 黄 / 红）
function masteryColor(mastery: number): string {
  if (mastery >= 100) return "#10B981"; // 翡翠绿
  if (mastery >= 50) return "#F59E0B";  // 琥珀黄
  return "#F43F5E";                      // 玫瑰红
}

const STAGE_LABELS: Record<number, string> = {
  1: "阶段一 · 入门",
  2: "阶段二 · 基础",
  3: "阶段三 · 进阶",
  4: "阶段四 · 实战",
  5: "阶段五 · 策略",
  6: "阶段六 · 心法",
};

const LEGEND = [
  { color: "#10B981", label: "已掌握 (≥100)" },
  { color: "#F59E0B", label: "部分掌握 (50-99)" },
  { color: "#F43F5E", label: "未掌握 (<50)" },
];

// ===================== 主组件 =====================

export function KnowledgeMap({ apiBase = "" }: KnowledgeMapProps) {
  const [nodes, setNodes] = useState<KnowledgeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`${apiBase}/api/knowledge-map`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        if (cancelled) return;
        const list: KnowledgeNode[] = Array.isArray(data)
          ? data
          : data?.nodes ?? [];
        setNodes(list);
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

  // 按 stage 分组（升序）
  const stages = useMemo(() => {
    const map = new Map<number, KnowledgeNode[]>();
    for (const n of nodes) {
      if (!map.has(n.stage)) map.set(n.stage, []);
      map.get(n.stage)!.push(n);
    }
    return Array.from(map.entries()).sort((a, b) => a[0] - b[0]);
  }, [nodes]);

  // 顶部总览统计
  const summary = useMemo(() => {
    const total = nodes.length;
    const mastered = nodes.filter((n) => n.mastery >= 100).length;
    const avg =
      total > 0
        ? Math.round(nodes.reduce((s, n) => s + n.mastery, 0) / total)
        : 0;
    return { total, mastered, avg };
  }, [nodes]);

  // ---------- 渲染 ----------

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="glass-card p-5 h-32 animate-pulse" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card p-6 text-center space-y-2">
        <p className="text-sm text-fg-muted">加载知识图谱失败</p>
        <p className="text-xs text-fg-dim">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* 顶部：图例 + 总览 */}
      <div className="glass-card specular-edge p-5 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-semibold text-fg">知识点图谱</h3>
          </div>
          <span className="text-xs text-fg-dim">
            共 {summary.total} 个知识点 · 已掌握 {summary.mastered} · 平均掌握度 {summary.avg}%
          </span>
        </div>

        {/* 图例 */}
        <div className="flex flex-wrap items-center gap-4">
          {LEGEND.map((l) => (
            <div
              key={l.label}
              className="flex items-center gap-1.5 text-xs text-fg-muted"
            >
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ background: l.color }}
              />
              {l.label}
            </div>
          ))}
        </div>
      </div>

      {/* 按阶段分组展示 */}
      {stages.length === 0 ? (
        <div className="glass-card p-8 text-center space-y-2">
          <Circle className="w-6 h-6 text-fg-dim mx-auto" />
          <p className="text-sm text-fg-muted">暂无知识点数据</p>
        </div>
      ) : (
        <div className="space-y-4">
          {stages.map(([stage, list]) => (
            <div key={stage} className="glass-card p-5 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-fg">
                  {STAGE_LABELS[stage] || `阶段 ${stage}`}
                </h4>
                <span className="text-xs text-fg-dim">
                  {list.filter((n) => n.mastery >= 100).length}/{list.length} 已掌握
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2.5">
                {list.map((n) => (
                  <div
                    key={n.id}
                    className="glass-light rounded-[12px] p-3 flex items-center gap-2.5 hover:bg-white/[0.08] transition group"
                    title={n.description || n.name}
                  >
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0 transition group-hover:scale-125"
                      style={{
                        background: masteryColor(n.mastery),
                        boxShadow: `0 0 8px ${masteryColor(n.mastery)}80`,
                      }}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-fg truncate">{n.name}</p>
                      <p className="text-[10px] text-fg-dim">{n.mastery}%</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
