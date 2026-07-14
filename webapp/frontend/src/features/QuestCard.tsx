/**
 * QuestCard.tsx --- 学习任务卡片组件
 *
 * 显示单个任务的标题、描述、XP 值、完成状态。
 * 完成时有勾选动画。
 */

import { Check, Circle } from "lucide-react";

export type QuestData = {
  id: string;
  chapter_id: string;
  title: string;
  type: string;
  xp: number;
  description: string;
  completed: boolean;
};

export function QuestCard({ quest }: { quest: QuestData }) {
  return (
    <div
      className={`flex items-start gap-3 px-3 py-2.5 rounded-lg border transition-colors ${
        quest.completed
          ? "border-emerald-500/30 bg-emerald-500/5"
          : "border-line bg-bg-subtle"
      }`}
    >
      {/* Status icon */}
      <div className="shrink-0 mt-0.5">
        {quest.completed ? (
          <Check className="h-4 w-4 text-emerald-400" />
        ) : (
          <Circle className="h-4 w-4 text-fg-dim" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p
          className={`text-sm leading-snug ${
            quest.completed ? "text-fg-muted line-through" : "text-fg"
          }`}
        >
          {quest.title}
        </p>
        <p className="text-xs text-fg-muted mt-0.5 leading-relaxed">
          {quest.description}
        </p>
      </div>

      {/* XP badge */}
      <span
        className={`shrink-0 text-[10px] font-semibold tabular px-1.5 py-0.5 rounded ${
          quest.completed
            ? "bg-emerald-500/10 text-emerald-400"
            : "bg-bg-hover text-fg-dim"
        }`}
      >
        +{quest.xp} XP
      </span>
    </div>
  );
}
