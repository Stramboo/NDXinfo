/**
 * Practice.tsx — 模拟练习入口 (Phase 4+5)
 *
 * 三层模式：引导式练习 → 情景训练 → 自由模拟
 */
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Gamepad2, FlaskConical, Compass } from "lucide-react";

interface ScenarioInfo {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  xp: number;
  steps_count: number;
}

const DIFFICULTY: Record<string, string> = {
  easy: "初",
  medium: "中",
};

export function Practice() {
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([]);

  useEffect(() => {
    fetch("/api/practice/scenarios")
      .then((r) => r.json())
      .then(setScenarios)
      .catch(() => {});
  }, []);

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 space-y-8">
      <div className="space-y-2">
        <p className="text-xs text-fg-muted uppercase tracking-wider">模拟练习</p>
        <h1 className="text-2xl font-bold text-fg">把知识变成行动</h1>
        <p className="text-sm text-fg-muted leading-relaxed">
          在这里，你可以用虚拟资金练习交易，不用担心亏钱。先学会做计划，再下单。
        </p>
      </div>

      {/* 练习模式卡片 */}
      <div className="space-y-3">
        {/* 引导式练习 */}
        <Link
          to="/practice/guided"
          className="block rounded-xl bg-bg-panel border border-emerald-500/20 p-5
                     hover:border-emerald-500/40 transition group"
        >
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center shrink-0">
              <Compass className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-fg">引导式练习</p>
              <p className="text-xs text-fg-muted mt-1">
                系统会一步步引导你完成第一笔模拟交易。
                选择公司 → 写理由 → 定仓位 → 下单。
              </p>
            </div>
            <span className="text-xs text-emerald-400 font-medium">推荐</span>
          </div>
        </Link>

        {/* 情景训练 — 动态列表 */}
        {scenarios.length > 0 && (
          <div className="rounded-xl bg-bg-panel border border-amber-500/20 p-5 space-y-3">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center shrink-0">
                <FlaskConical className="w-5 h-5 text-amber-400" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-fg">情景训练</p>
                <p className="text-xs text-fg-muted mt-1">
                  在预设的市场场景中练习判断。选择场景开始训练。
                </p>
              </div>
            </div>
            <div className="space-y-2 pt-1">
              {scenarios.map((s) => (
                <Link
                  key={s.id}
                  to={`/practice/scenario/${s.id}`}
                  className="flex items-center gap-3 rounded-lg bg-bg-subtle p-3 hover:bg-amber-500/5 transition border border-line hover:border-amber-500/20"
                >
                  <span className="shrink-0 w-6 h-6 rounded-md bg-amber-500/10 flex items-center justify-center text-[10px] font-bold text-amber-400">
                    {DIFFICULTY[s.difficulty] || "?"}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-fg truncate">{s.title}</p>
                    <p className="text-xs text-fg-dim truncate">{s.description}</p>
                  </div>
                  <span className="text-xs text-fg-dim shrink-0">{s.xp} XP</span>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* 自由模拟 */}
        <div className="rounded-xl bg-bg-panel border border-line p-5 opacity-60">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center shrink-0">
              <Gamepad2 className="w-5 h-5 text-purple-400" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-fg">自由模拟</p>
              <p className="text-xs text-fg-muted mt-1">
                完成基础课程后解锁。可自由选择股票、策略和技术指标进行模拟交易。
              </p>
            </div>
            <span className="text-xs text-fg-dim">学完课程解锁</span>
          </div>
        </div>
      </div>

      {/* 引导提示 */}
      <div className="p-4 rounded-xl bg-blue-500/5 border border-blue-500/20 space-y-1">
        <p className="text-xs text-blue-300 font-medium">💡 提示</p>
        <p className="text-xs text-fg-muted leading-relaxed">
          建议先完成「学习」中的基础课程，再来做练习。每笔交易前，想清楚你为什么买、准备持有多久、什么情况下会卖出。
        </p>
      </div>
    </div>
  );
}
