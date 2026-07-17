/**
 * StageExam.tsx — 阶段结业考试页面 (v2.4 Phase 5)
 */
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Lock, Award } from "lucide-react";
import { QuizRunner } from "../features/QuizRunner";

interface ExamData {
  title: string;
  pass_score: number;
  questions: { question: string; options: string[] }[];
  chapters_required: number;
  chapters_completed: number;
  unlocked: boolean;
  best_score: number | null;
  already_passed: boolean;
}

export function StageExam() {
  const { stageId } = useParams<{ stageId: string }>();
  const [exam, setExam] = useState<ExamData | null>(null);
  const [loading, setLoading] = useState(true);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    fetch(`/api/learning/exams/${stageId}`)
      .then((r) => r.json())
      .then(setExam)
      .catch(() => setExam(null))
      .finally(() => setLoading(false));
  }, [stageId]);

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 space-y-4">
        <div className="h-8 w-48 rounded bg-white/[0.06] animate-pulse" />
        <div className="h-64 glass-card animate-pulse" />
      </div>
    );
  }

  if (!exam) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 text-center">
        <p className="text-fg-muted">考试不存在</p>
        <Link to="/learning" className="text-emerald-400 text-sm mt-2 inline-block">← 返回学习</Link>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
      <div>
        <Link to="/learning" className="text-xs text-fg-dim hover:text-fg transition">← 返回学习</Link>
        <h1 className="text-xl font-bold text-fg mt-1 tracking-tight">{exam.title}</h1>
      </div>

      {!started ? (
        <div className="glass-card specular-edge p-6 space-y-4 text-center">
          <div className="w-16 h-16 mx-auto rounded-full bg-emerald-500/15 flex items-center justify-center">
            {exam.unlocked
              ? <Award className="w-8 h-8 text-emerald-400" />
              : <Lock className="w-8 h-8 text-fg-dim" />}
          </div>

          {exam.unlocked ? (
            <>
              <div className="space-y-1">
                <p className="text-lg font-semibold text-fg">准备好了吗？</p>
                <p className="text-sm text-fg-muted">
                  共 {exam.questions.length} 题 · {exam.pass_score} 分通过
                </p>
                {exam.best_score !== null && (
                  <p className="text-xs text-fg-dim">
                    历史最佳：{exam.best_score} 分 {exam.already_passed && "（已通过 ✓）"}
                  </p>
                )}
              </div>
              <button
                onClick={() => setStarted(true)}
                className="glass-btn-primary px-8 py-3 rounded-[14px] text-sm font-bold"
              >
                {exam.already_passed ? "再考一次" : "开始考试"}
              </button>
            </>
          ) : (
            <div className="space-y-2">
              <p className="text-lg font-semibold text-fg">尚未解锁</p>
              <p className="text-sm text-fg-muted">
                需先完成本阶段全部课程（{exam.chapters_completed}/{exam.chapters_required}）
              </p>
              <Link to="/learning" className="glass-btn inline-block px-6 py-2.5 rounded-[12px] text-sm text-fg mt-2">
                去学习
              </Link>
            </div>
          )}
        </div>
      ) : (
        <div className="glass-card p-6">
          <QuizRunner
            title={exam.title}
            questions={exam.questions}
            submitUrl={`/api/learning/exams/${stageId}/submit`}
            passScore={exam.pass_score}
            onClose={() => setStarted(false)}
          />
        </div>
      )}
    </div>
  );
}
