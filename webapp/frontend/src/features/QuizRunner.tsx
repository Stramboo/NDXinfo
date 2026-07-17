/**
 * QuizRunner.tsx — 测验/考试答题组件 (v2.4 Phase 5)
 *
 * 多题顺序作答 → 即时判分 → 成绩页（含解析）
 */
import { useState } from "react";
import { CheckCircle2, XCircle, Award } from "lucide-react";

interface Question {
  question: string;
  options: string[];
}

interface QuizResult {
  score: number;
  correct_count: number;
  total_questions: number;
  passed: boolean;
  xp_earned?: number;
  details: {
    question: string;
    your_answer: number;
    correct_answer: number;
    is_correct: boolean;
    explanation: string;
  }[];
}

interface QuizRunnerProps {
  title: string;
  questions: Question[];
  submitUrl: string;   // POST 提交地址
  passScore?: number;
  onClose?: () => void;
}

export function QuizRunner({ title, questions, submitUrl, passScore = 60, onClose }: QuizRunnerProps) {
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const q = questions[current];
  const isLast = current === questions.length - 1;

  const handleNext = async () => {
    if (selected === null) return;
    const newAnswers = [...answers, selected];
    setAnswers(newAnswers);
    setSelected(null);

    if (!isLast) {
      setCurrent(current + 1);
      return;
    }

    // 提交
    setSubmitting(true);
    try {
      const res = await fetch(submitUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers: newAnswers }),
      });
      const data = await res.json();
      setResult(data);
    } catch {
      setResult(null);
    } finally {
      setSubmitting(false);
    }
  };

  // ---- 成绩页 ----
  if (result) {
    return (
      <div className="space-y-4">
        <div className="text-center space-y-2 py-4">
          <div className={`w-16 h-16 mx-auto rounded-full flex items-center justify-center ${
            result.passed ? "bg-emerald-500/15" : "bg-rose-500/15"
          }`}>
            <Award className={`w-8 h-8 ${result.passed ? "text-emerald-400" : "text-rose-400"}`} />
          </div>
          <p className={`text-3xl font-bold ${result.passed ? "text-emerald-400" : "text-rose-400"}`}>
            {result.score} 分
          </p>
          <p className="text-sm text-fg-muted">
            答对 {result.correct_count}/{result.total_questions} 题
            {result.passed ? " · 通过 🎉" : ` · ${passScore} 分通过`}
          </p>
          {(result.xp_earned ?? 0) > 0 && (
            <p className="text-xs text-amber-400">+{result.xp_earned} XP</p>
          )}
        </div>

        {/* 逐题解析 */}
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {result.details.map((d, i) => (
            <div key={i} className={`glass-light rounded-[12px] p-3 text-xs ${
              d.is_correct ? "" : "border-rose-400/20"
            }`}>
              <div className="flex items-start gap-2">
                {d.is_correct
                  ? <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  : <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />}
                <div className="space-y-1">
                  <p className="text-fg font-medium">{d.question}</p>
                  {!d.is_correct && (
                    <p className="text-fg-muted">
                      正确答案：{questions[i]?.options[d.correct_answer]}
                    </p>
                  )}
                  <p className="text-fg-dim">{d.explanation}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {onClose && (
          <button onClick={onClose}
                  className="glass-btn-primary w-full py-2.5 rounded-[12px] text-sm font-semibold">
            完成
          </button>
        )}
      </div>
    );
  }

  // ---- 答题页 ----
  return (
    <div className="space-y-4">
      {/* 进度 */}
      <div className="flex items-center justify-between text-xs text-fg-dim">
        <span>{title}</span>
        <span className="tabular">{current + 1}/{questions.length}</span>
      </div>
      <div className="h-1 rounded-full bg-white/[0.06] overflow-hidden">
        <div className="h-full bg-gradient-to-r from-emerald-400 to-emerald-500 transition-all duration-300"
             style={{ width: `${((current + 1) / questions.length) * 100}%` }} />
      </div>

      {/* 题目 */}
      <p className="text-sm font-semibold text-fg leading-relaxed">{q.question}</p>

      {/* 选项 */}
      <div className="space-y-2">
        {q.options.map((opt, i) => (
          <button
            key={i}
            onClick={() => setSelected(i)}
            className={`w-full text-left px-4 py-3 rounded-[12px] text-sm transition-all duration-200 ${
              selected === i
                ? "bg-emerald-500/15 border border-emerald-400/40 text-fg"
                : "glass-light text-fg-muted hover:text-fg hover:bg-white/[0.08]"
            }`}
          >
            <span className="inline-block w-5 text-fg-dim">{String.fromCharCode(65 + i)}.</span>
            {opt}
          </button>
        ))}
      </div>

      {/* 下一题/提交 */}
      <button
        onClick={handleNext}
        disabled={selected === null || submitting}
        className="glass-btn-primary w-full py-2.5 rounded-[12px] text-sm font-semibold
                   disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {submitting ? "判分中..." : isLast ? "提交" : "下一题"}
      </button>
    </div>
  );
}
