/**
 * Onboarding.tsx --- Single-screen intro card (not a wizard).
 *
 * Shown once on first visit. Sets `onboarding_completed` in localStorage.
 * Clean dark background, serif-style title, minimal copy, single CTA.
 */

import { useState, useEffect } from "react";
import { ArrowRight } from "lucide-react";

const STORAGE_KEY = "onboarding_completed";

export function Onboarding({ onDone }: { onDone: () => void }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Check if already completed
    const done = localStorage.getItem(STORAGE_KEY);
    if (done === "1") {
      onDone();
      return;
    }
    // Small delay for smooth entry
    const t = setTimeout(() => setVisible(true), 80);
    return () => clearTimeout(t);
  }, []);

  function handleStart() {
    localStorage.setItem(STORAGE_KEY, "1");
    setVisible(false);
    setTimeout(onDone, 300);
  }

  return (
    <div
      className={
        "fixed inset-0 z-50 flex items-center justify-center transition-all duration-500 bg-bg " +
        (visible ? "opacity-100" : "opacity-0 pointer-events-none")
      }
    >
      <div className="w-full max-w-lg px-8 py-14 text-center">
        {/* Brand mark */}
        <div className="mb-8">
          <h1
            className="text-7xl font-light tracking-tight text-fg"
            style={{ fontFamily: '"Georgia", "Noto Serif SC", serif' }}
          >
            NDX
          </h1>
          <p className="mt-3 text-base text-fg-muted tracking-wide">
            股票交易与学习工具
          </p>
        </div>

        {/* Divider */}
        <div className="w-12 h-px bg-line mx-auto my-8" />

        {/* Description */}
        <div className="space-y-4 text-left text-sm leading-relaxed text-fg-muted px-2">
          <p>
            股票市场是世界上最具活力的金融市场之一。
            在这里，你可以学习如何分析股票趋势、理解技术指标，
            并在模拟环境中练习交易决策——无需承担真实资金风险。
          </p>
          <p>
            本平台提供一个完全独立的<strong className="text-fg">演示账户</strong>，
            初始资金为 $100,000。你可以自由买卖股票，
            观察持仓变化，追踪净值曲线。
            所有数据均为模拟数据，帮助你安全地积累经验。
          </p>
        </div>

        {/* CTA */}
        <button
          onClick={handleStart}
          className="mt-10 inline-flex items-center gap-2 px-8 py-3 rounded-lg
                     bg-emerald-500 text-bg font-semibold text-sm
                     hover:bg-emerald-400 transition-colors tracking-wide"
        >
          开始
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
