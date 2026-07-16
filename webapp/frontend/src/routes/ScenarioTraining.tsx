/**
 * ScenarioTraining.tsx — 情景训练页面 (Phase 5)
 *
 * 分支决策式的情景训练：加载场景 → 逐步决策 → 评估反馈
 */
import { useState, useEffect, useCallback } from "react";
import { useParams, Link } from "react-router-dom";

interface ScenarioStep {
  id: string;
  question: string;
  options: { id: string; text: string; result: string; feedback: string }[];
}

interface Scenario {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  xp: number;
  context: Record<string, string>;
  steps: ScenarioStep[];
  takeaway: string;
}

interface Decision {
  step: string;
  choice: string;
  result: string;
}

interface EvalResult {
  score: number;
  level: string;
  total_steps: number;
  good_decisions: number;
  partial_decisions: number;
  bad_decisions: number;
  feedback: string[];
  scenario_title: string;
  xp_earned: number;
  takeaway: string;
}

const DIFFICULTY: Record<string, string> = {
  easy: "初级",
  medium: "中级",
};

export function ScenarioTraining() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [step, setStep] = useState(0);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [evalResult, setEvalResult] = useState<EvalResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!scenarioId) return;
    fetch(`/api/practice/scenarios/${scenarioId}`)
      .then((r) => r.json())
      .then((d) => {
        setScenario(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [scenarioId]);

  const currentStep = scenario?.steps[step];

  const handleSelect = useCallback(
    (optionId: string) => {
      if (!currentStep || showFeedback) return;
      setSelectedOption(optionId);
      const opt = currentStep.options.find((o) => o.id === optionId);
      if (opt) {
        setDecisions((prev) => [
          ...prev,
          { step: currentStep.id, choice: optionId, result: opt.result },
        ]);
      }
      setShowFeedback(true);
    },
    [currentStep, showFeedback]
  );

  const handleNext = useCallback(() => {
    if (!scenario) return;
    if (step + 1 >= scenario.steps.length) {
      // 评估
      fetch(`/api/practice/scenarios/${scenarioId}/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decisions }),
      })
        .then((r) => r.json())
        .then(setEvalResult);
    } else {
      setStep((s) => s + 1);
      setSelectedOption(null);
      setShowFeedback(false);
    }
  }, [step, scenario, decisions, scenarioId]);

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 space-y-4">
        <div className="h-6 w-32 rounded bg-bg-subtle animate-pulse" />
        <div className="h-8 w-64 rounded bg-bg-subtle animate-pulse" />
        <div className="h-48 rounded-xl bg-bg-panel animate-pulse" />
      </div>
    );
  }

  if (!scenario) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 text-center text-fg-dim">
        <p>情景未找到</p>
        <Link to="/practice" className="text-emerald-400 hover:underline text-sm mt-2 inline-block">
          ← 返回练习
        </Link>
      </div>
    );
  }

  // 结果页
  if (evalResult) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
        <div className="text-center space-y-4">
          <div className="text-5xl">
            {evalResult.score >= 80 ? "🎉" : evalResult.score >= 50 ? "👍" : "💪"}
          </div>
          <h1 className="text-2xl font-bold text-fg">{evalResult.scenario_title} — 完成！</h1>
          <p className="text-lg text-fg-muted">
            得分 <span className="text-emerald-400 font-bold">{evalResult.score}</span> 分 ·{" "}
            {evalResult.level}
          </p>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-4 text-center">
            <p className="text-2xl font-bold text-emerald-400">{evalResult.good_decisions}</p>
            <p className="text-[10px] text-fg-dim mt-1">优秀决策</p>
          </div>
          <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-4 text-center">
            <p className="text-2xl font-bold text-amber-400">{evalResult.partial_decisions}</p>
            <p className="text-[10px] text-fg-dim mt-1">部分正确</p>
          </div>
          <div className="rounded-xl bg-rose-500/10 border border-rose-500/20 p-4 text-center">
            <p className="text-2xl font-bold text-rose-400">{evalResult.bad_decisions}</p>
            <p className="text-[10px] text-fg-dim mt-1">需要改进</p>
          </div>
        </div>

        <div className="rounded-xl bg-bg-panel border border-line p-5 space-y-2">
          <p className="text-xs text-fg-muted uppercase tracking-wider">关键收获</p>
          <p className="text-sm text-fg leading-relaxed">{evalResult.takeaway}</p>
          {evalResult.feedback.length > 0 && !evalResult.feedback.includes("做得很好！") && (
            <div className="mt-3 pt-3 border-t border-line">
              <p className="text-xs text-amber-400 mb-1">改进建议：</p>
              {evalResult.feedback.map((f, i) => (
                <p key={i} className="text-xs text-fg-muted">• {f}</p>
              ))}
            </div>
          )}
        </div>

        <div className="flex gap-3 justify-center">
          <Link
            to="/practice"
            className="px-4 py-2 rounded-lg bg-bg-subtle text-sm text-fg hover:bg-bg-panel transition"
          >
            返回练习
          </Link>
          <button
            onClick={() => {
              setStep(0);
              setDecisions([]);
              setSelectedOption(null);
              setShowFeedback(false);
              setEvalResult(null);
            }}
            className="px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-sm text-emerald-400 hover:bg-emerald-500/20 transition"
          >
            重新挑战
          </button>
        </div>
      </div>
    );
  }

  const selectedOpt = selectedOption
    ? currentStep?.options.find((o) => o.id === selectedOption)
    : null;

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
      {/* 面包屑 */}
      <div className="flex items-center gap-2 text-xs text-fg-dim">
        <Link to="/practice" className="hover:text-fg transition">
          练习
        </Link>
        <span>/</span>
        <span className="text-fg">情景训练</span>
      </div>

      {/* 头部 */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs px-2 py-0.5 rounded bg-bg-subtle text-fg-dim">
            {DIFFICULTY[scenario.difficulty] || scenario.difficulty}
          </span>
          <span className="text-xs text-fg-muted">{scenario.xp} XP</span>
        </div>
        <h1 className="text-xl font-bold text-fg">{scenario.title}</h1>
        <p className="text-sm text-fg-muted">{scenario.description}</p>
      </div>

      {/* 进度 */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1.5 rounded-full bg-bg-subtle overflow-hidden">
          <div
            className="h-full bg-emerald-500 rounded-full transition-all duration-300"
            style={{ width: `${((step + 1) / scenario.steps.length) * 100}%` }}
          />
        </div>
        <span className="text-xs text-fg-dim tabular-nums">
          {step + 1}/{scenario.steps.length}
        </span>
      </div>

      {/* 决策卡片 */}
      {currentStep && (
        <div className="rounded-xl bg-bg-panel border border-line p-6 space-y-4">
          <p className="text-sm font-medium text-fg leading-relaxed">
            {currentStep.question}
          </p>

          <div className="space-y-2">
            {currentStep.options.map((opt) => {
              const isSelected = selectedOption === opt.id;
              const isRevealed = showFeedback;
              const resultColor =
                opt.result === "good"
                  ? "border-emerald-500/50 bg-emerald-500/10"
                  : opt.result === "bad"
                  ? "border-rose-500/50 bg-rose-500/10"
                  : "border-amber-500/50 bg-amber-500/10";

              return (
                <div key={opt.id}>
                  <button
                    onClick={() => handleSelect(opt.id)}
                    disabled={showFeedback}
                    className={`w-full text-left p-3 rounded-lg border transition-all text-sm ${
                      isSelected && isRevealed
                        ? resultColor
                        : isSelected
                        ? "border-emerald-500 bg-emerald-500/5 text-fg"
                        : "border-line bg-bg-subtle text-fg-muted hover:border-emerald-500/30 hover:bg-bg-subtle"
                    } ${showFeedback && !isSelected ? "opacity-50" : ""}`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-5 text-center text-xs font-mono text-fg-dim">
                        {opt.id.toUpperCase()}
                      </span>
                      <span>{opt.text}</span>
                    </div>
                  </button>
                  {isSelected && showFeedback && opt.feedback && (
                    <div
                      className={`mt-1 ml-7 p-2 rounded text-xs ${
                        opt.result === "good"
                          ? "text-emerald-400 bg-emerald-500/5"
                          : opt.result === "bad"
                          ? "text-rose-400 bg-rose-500/5"
                          : "text-amber-400 bg-amber-500/5"
                      }`}
                    >
                      {opt.result === "good" ? "✓ " : opt.result === "bad" ? "✗ " : "△ "}
                      {opt.feedback}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {showFeedback && (
            <button
              onClick={handleNext}
              className="w-full py-2.5 rounded-lg bg-emerald-500 text-white text-sm font-medium hover:bg-emerald-600 transition mt-2"
            >
              {step + 1 >= scenario.steps.length ? "查看结果" : "下一步 →"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
