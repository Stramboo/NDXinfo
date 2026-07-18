/**
 * EmotionTraining.tsx — 情绪训练页面
 *
 * 列表 + 详情双视图：
 *   - 列表：fetch /api/emotion-scenarios，展示所有情绪场景卡片
 *           （图标 + 标题 + 情绪类型 + 难度）
 *   - 详情：fetch /api/emotion-scenarios/:id，展示场景描述 + 情绪上下文
 *           （压力等级等），逐步决策答题
 *
 * 流程：pre_emotion 滑块 → 逐步决策 → post_emotion + 反思 → 评估结果
 * 完成后展示：评分 + 情绪课程 + 理性度评分。
 */
import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  Brain,
  Flame,
  Activity,
  ArrowRight,
} from "lucide-react";

// ---------- 类型定义 ----------

interface EmotionScenarioSummary {
  id: string;
  title: string;
  icon?: string;
  emotion_type: string;     // fear | greed | fomo | panic | ...
  difficulty: string;       // easy | medium | hard
  xp: number;
}

interface EmotionStepOption {
  id: string;
  text: string;
  result?: "good" | "partial" | "bad";
  feedback?: string;
}

interface EmotionStep {
  id: string;
  question: string;
  context?: string;
  options: EmotionStepOption[];
}

interface EmotionContext {
  pressure_level?: number;     // 1-10
  market_volatility?: string;
  loss_exposure?: string;
  [k: string]: unknown;
}

interface EmotionScenarioDetail extends EmotionScenarioSummary {
  description: string;
  context: EmotionContext;
  steps: EmotionStep[];
  emotion_lesson?: string;
}

interface EmotionResult {
  score: number;
  rationality_score: number; // 理性度评分 0-100
  level: string;
  emotion_lesson: string;
  feedback: string[];
  xp_earned: number;
}

const DIFFICULTY_LABEL: Record<string, string> = {
  easy: "初级",
  medium: "中级",
  hard: "高级",
};

const EMOTION_LABEL: Record<string, string> = {
  fear: "恐惧",
  greed: "贪婪",
  fomo: "FOMO",
  panic: "恐慌",
  hope: "希望",
  regret: "懊悔",
  overconfidence: "过度自信",
};

const EMOTION_COLOR: Record<string, string> = {
  fear: "text-blue-400",
  greed: "text-amber-400",
  fomo: "text-purple-400",
  panic: "text-rose-400",
  hope: "text-emerald-400",
  regret: "text-fg-muted",
  overconfidence: "text-orange-400",
};

type Phase = "pre" | "steps" | "reflection" | "result";

// ===================== 主组件（列表） =====================

export function EmotionTraining() {
  const [scenarios, setScenarios] = useState<EmotionScenarioSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch("/api/emotion-scenarios")
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        if (cancelled) return;
        const list: EmotionScenarioSummary[] = Array.isArray(data)
          ? data
          : data?.scenarios ?? [];
        setScenarios(list);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // 进入详情
  if (selectedId) {
    return (
      <EmotionDetail
        scenarioId={selectedId}
        onBack={() => setSelectedId(null)}
      />
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-6">
      {/* 面包屑 */}
      <div className="flex items-center gap-2 text-xs text-fg-dim">
        <Link to="/practice" className="hover:text-fg transition">
          练习
        </Link>
        <span>/</span>
        <span className="text-fg">情绪训练</span>
      </div>

      <header className="space-y-1">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-emerald-400" />
          <h1 className="text-xl font-bold text-fg">情绪训练</h1>
        </div>
        <p className="text-sm text-fg-muted">
          在高压情境下识别情绪干扰，锻炼理性决策能力。
        </p>
      </header>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="glass-card h-32 animate-pulse" />
          ))}
        </div>
      ) : scenarios.length === 0 ? (
        <div className="glass-card p-8 text-center space-y-2">
          <Flame className="w-8 h-8 text-fg-dim mx-auto" />
          <p className="text-sm text-fg-muted">暂无情绪训练场景</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {scenarios.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelectedId(s.id)}
              className="glass-card specular-edge p-4 text-left space-y-3 hover:border-emerald-500/40 transition"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{s.icon || "🎭"}</span>
                  <div>
                    <p className="text-sm font-semibold text-fg">{s.title}</p>
                    <p
                      className={`text-xs ${
                        EMOTION_COLOR[s.emotion_type] || "text-fg-muted"
                      }`}
                    >
                      {EMOTION_LABEL[s.emotion_type] || s.emotion_type}
                    </p>
                  </div>
                </div>
                <span className="text-xs text-amber-400 shrink-0">
                  +{s.xp} XP
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="glass-pill px-2 py-0.5 rounded-full text-[10px] text-fg-muted">
                  {DIFFICULTY_LABEL[s.difficulty] || s.difficulty}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ===================== 详情组件 =====================

function EmotionDetail({
  scenarioId,
  onBack,
}: {
  scenarioId: string;
  onBack: () => void;
}) {
  const [scenario, setScenario] = useState<EmotionScenarioDetail | null>(null);
  const [loading, setLoading] = useState(true);

  // 流程阶段
  const [phase, setPhase] = useState<Phase>("pre");
  const [preEmotion, setPreEmotion] = useState(5);
  const [postEmotion, setPostEmotion] = useState(5);
  const [reflection, setReflection] = useState("");

  // 答题状态
  const [step, setStep] = useState(0);
  const [decisions, setDecisions] = useState<
    { step: string; choice: string; result: string }[]
  >([]);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);

  const [result, setResult] = useState<EmotionResult | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // 拉取详情
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`/api/emotion-scenarios/${scenarioId}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (cancelled) return;
        setScenario(d);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [scenarioId]);

  const currentStep = scenario?.steps[step];

  // 选择选项
  const handleSelect = useCallback(
    (optionId: string) => {
      if (!currentStep || showFeedback) return;
      const opt = currentStep.options.find((o) => o.id === optionId);
      if (!opt) return;
      setSelectedOption(optionId);
      setDecisions((prev) => [
        ...prev,
        {
          step: currentStep.id,
          choice: optionId,
          result: opt.result || "neutral",
        },
      ]);
      setShowFeedback(true);
    },
    [currentStep, showFeedback]
  );

  // 进入下一步或反思阶段
  const handleNext = useCallback(() => {
    if (!scenario) return;
    if (step + 1 >= scenario.steps.length) {
      setPhase("reflection");
    } else {
      setStep((s) => s + 1);
      setSelectedOption(null);
      setShowFeedback(false);
    }
  }, [step, scenario]);

  // 提交最终评估
  const submitFinal = useCallback(async () => {
    if (!scenario) return;
    setSubmitting(true);
    try {
      const res = await fetch(
        `/api/emotion-scenarios/${scenarioId}/evaluate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            decisions,
            pre_emotion: preEmotion,
            post_emotion: postEmotion,
            reflection,
          }),
        }
      );
      if (res.ok) {
        const data = await res.json();
        setResult(data as EmotionResult);
        setPhase("result");
      }
    } finally {
      setSubmitting(false);
    }
  }, [scenario, decisions, preEmotion, postEmotion, reflection, scenarioId]);

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 space-y-4">
        <div className="h-6 w-32 rounded bg-bg-subtle animate-pulse" />
        <div className="h-48 rounded-xl bg-bg-panel animate-pulse" />
      </div>
    );
  }

  if (!scenario) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 text-center space-y-2">
        <p className="text-sm text-fg-dim">情绪训练场景未找到</p>
        <button
          onClick={onBack}
          className="text-xs text-emerald-400 hover:underline"
        >
          ← 返回列表
        </button>
      </div>
    );
  }

  // ---------- 结果页 ----------
  if (phase === "result" && result) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
        <div className="text-center space-y-3">
          <div className="text-5xl">
            {result.score >= 80 ? "🧘" : result.score >= 50 ? "🤔" : "😤"}
          </div>
          <h1 className="text-xl font-bold text-fg">
            {scenario.title} — 完成！
          </h1>
          <p className="text-lg text-fg-muted">
            得分 <span className="text-emerald-400 font-bold">{result.score}</span>{" "}
            分 · {result.level}
          </p>
        </div>

        {/* 理性度评分 */}
        <div className="glass-card specular-edge p-5 space-y-2 text-center">
          <div className="flex items-center justify-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <p className="text-xs text-fg-muted uppercase tracking-wider">
              理性度评分
            </p>
          </div>
          <p
            className={`text-3xl font-bold ${
              result.rationality_score >= 70
                ? "text-emerald-400"
                : result.rationality_score >= 40
                ? "text-amber-400"
                : "text-rose-400"
            }`}
          >
            {result.rationality_score}
          </p>
          {/* 情绪变化对比 */}
          <div className="flex items-center justify-center gap-6 text-xs text-fg-dim mt-2">
            <span>
              开始前情绪{" "}
              <span className="text-fg">{preEmotion}/10</span>
            </span>
            <ArrowRight className="w-3 h-3" />
            <span>
              结束后情绪{" "}
              <span className="text-fg">{postEmotion}/10</span>
            </span>
          </div>
        </div>

        {/* 情绪课程 */}
        {result.emotion_lesson && (
          <div className="glass-card p-5 space-y-2">
            <p className="text-xs text-fg-muted uppercase tracking-wider">
              情绪课程
            </p>
            <p className="text-sm text-fg leading-relaxed">
              {result.emotion_lesson}
            </p>
          </div>
        )}

        {/* 反馈 */}
        {result.feedback.length > 0 && (
          <div className="glass-card p-5 space-y-2">
            <p className="text-xs text-fg-muted uppercase tracking-wider">
              改进建议
            </p>
            {result.feedback.map((f, i) => (
              <p key={i} className="text-xs text-fg-muted">
                • {f}
              </p>
            ))}
          </div>
        )}

        <div className="flex gap-3 justify-center">
          <button
            onClick={onBack}
            className="glass-btn px-4 py-2 rounded-[12px] text-sm text-fg"
          >
            返回列表
          </button>
          <button
            onClick={() => {
              setStep(0);
              setDecisions([]);
              setSelectedOption(null);
              setShowFeedback(false);
              setResult(null);
              setPhase("pre");
              setReflection("");
            }}
            className="glass-btn-primary px-4 py-2 rounded-[12px] text-sm font-semibold"
          >
            重新挑战
          </button>
        </div>
      </div>
    );
  }

  // ---------- 反思页 ----------
  if (phase === "reflection") {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
        <button
          onClick={onBack}
          className="text-xs text-fg-dim hover:text-fg transition flex items-center gap-1.5"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> 返回列表
        </button>

        <div className="glass-card specular-edge p-6 space-y-5">
          <h2 className="text-base font-semibold text-fg">
            完成训练，记录你的情绪变化
          </h2>

          {/* Post emotion 滑块 */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-fg-muted">
                现在你的情绪强度（1=平静，10=激动）
              </span>
              <span className="text-emerald-400 font-bold text-sm tabular">
                {postEmotion}
              </span>
            </div>
            <input
              type="range"
              min={1}
              max={10}
              value={postEmotion}
              onChange={(e) => setPostEmotion(Number(e.target.value))}
              className="w-full accent-emerald-500"
            />
          </div>

          {/* 反思 */}
          <div className="space-y-2">
            <p className="text-xs text-fg-muted">
              回顾刚才的决策，写下你的反思：
            </p>
            <textarea
              value={reflection}
              onChange={(e) => setReflection(e.target.value)}
              placeholder="例如：我注意到在压力下我倾向于..."
              rows={4}
              className="w-full bg-bg-input border border-line rounded-[12px] px-3 py-2 text-sm text-fg resize-none focus:outline-none focus:border-emerald-500"
            />
          </div>

          <button
            onClick={submitFinal}
            disabled={submitting}
            className="glass-btn-primary w-full py-2.5 rounded-[12px] text-sm font-semibold disabled:opacity-40"
          >
            {submitting ? "评估中..." : "查看结果"}
          </button>
        </div>
      </div>
    );
  }

  // ---------- Pre-emotion 滑块页 ----------
  if (phase === "pre") {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
        <button
          onClick={onBack}
          className="text-xs text-fg-dim hover:text-fg transition flex items-center gap-1.5"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> 返回列表
        </button>

        <div className="space-y-2">
          <span className="glass-pill px-2 py-0.5 rounded-full text-[10px] text-fg-muted">
            {DIFFICULTY_LABEL[scenario.difficulty] || scenario.difficulty}
          </span>
          <h1 className="text-xl font-bold text-fg">{scenario.title}</h1>
          <p className="text-sm text-fg-muted">{scenario.description}</p>
        </div>

        {/* 情绪上下文 */}
        {scenario.context && (
          <div className="glass-card p-5 space-y-2">
            <p className="text-xs text-fg-muted uppercase tracking-wider">
              情绪上下文
            </p>
            {scenario.context.pressure_level !== undefined && (
              <div className="flex items-center gap-2 text-sm">
                <Flame className="w-4 h-4 text-rose-400" />
                <span className="text-fg-muted">压力等级</span>
                <span className="text-fg font-semibold">
                  {scenario.context.pressure_level}/10
                </span>
              </div>
            )}
            {scenario.context.market_volatility && (
              <div className="text-xs text-fg-muted">
                市场波动：{scenario.context.market_volatility}
              </div>
            )}
            {scenario.context.loss_exposure && (
              <div className="text-xs text-fg-muted">
                亏损暴露：{scenario.context.loss_exposure}
              </div>
            )}
          </div>
        )}

        {/* Pre emotion 滑块 */}
        <div className="glass-card specular-edge p-6 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-fg-muted">
              开始前你的情绪强度（1=平静，10=激动）
            </span>
            <span className="text-emerald-400 font-bold text-sm tabular">
              {preEmotion}
            </span>
          </div>
          <input
            type="range"
            min={1}
            max={10}
            value={preEmotion}
            onChange={(e) => setPreEmotion(Number(e.target.value))}
            className="w-full accent-emerald-500"
          />
          <button
            onClick={() => setPhase("steps")}
            className="glass-btn-primary w-full py-2.5 rounded-[12px] text-sm font-semibold"
          >
            开始训练
          </button>
        </div>
      </div>
    );
  }

  // ---------- 决策答题页 ----------
  const selectedOpt = selectedOption
    ? currentStep?.options.find((o) => o.id === selectedOption)
    : null;

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
      <button
        onClick={onBack}
        className="text-xs text-fg-dim hover:text-fg transition flex items-center gap-1.5"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> 返回列表
      </button>

      <header className="space-y-1">
        <h1 className="text-lg font-bold text-fg">{scenario.title}</h1>
      </header>

      {/* 进度 */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1.5 rounded-full bg-bg-subtle overflow-hidden">
          <div
            className="h-full bg-emerald-500 rounded-full transition-all duration-300"
            style={{
              width: `${((step + 1) / scenario.steps.length) * 100}%`,
            }}
          />
        </div>
        <span className="text-xs text-fg-dim tabular">
          {step + 1}/{scenario.steps.length}
        </span>
      </div>

      {currentStep && (
        <div className="glass-card specular-edge p-6 space-y-4">
          {currentStep.context && (
            <div className="glass-light rounded-[12px] p-3 text-xs text-fg-muted">
              {currentStep.context}
            </div>
          )}
          <p className="text-sm font-medium text-fg leading-relaxed">
            {currentStep.question}
          </p>

          <div className="space-y-2">
            {currentStep.options.map((opt) => {
              const isSelected = selectedOption === opt.id;
              const resultColor =
                opt.result === "good"
                  ? "border-emerald-500/50 bg-emerald-500/10"
                  : opt.result === "bad"
                  ? "border-rose-500/50 bg-rose-500/10"
                  : opt.result === "partial"
                  ? "border-amber-500/50 bg-amber-500/10"
                  : "border-emerald-500 bg-emerald-500/5";

              return (
                <div key={opt.id}>
                  <button
                    onClick={() => handleSelect(opt.id)}
                    disabled={showFeedback}
                    className={`w-full text-left p-3 rounded-[12px] border text-sm transition-all ${
                      isSelected && showFeedback
                        ? resultColor
                        : isSelected
                        ? "border-emerald-500 bg-emerald-500/5 text-fg"
                        : "border-line glass-light text-fg-muted hover:border-emerald-500/30 hover:text-fg"
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
                      {opt.result === "good"
                        ? "✓ "
                        : opt.result === "bad"
                        ? "✗ "
                        : "△ "}
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
              className="glass-btn-primary w-full py-2.5 rounded-[12px] text-sm font-semibold"
            >
              {step + 1 >= scenario.steps.length ? "完成训练" : "下一步 →"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
