/**
 * ScenarioQuestionRunner.tsx — 情景判断题答题器
 *
 * 支持 4 种题型：
 *   - multi     多选题（checkbox 多选）
 *   - sort      排序题（点击列表按顺序选中）
 *   - match     匹配题（左右两列点击配对）
 *   - branching 分支题（选择后展示子问题）
 *
 * 答题完成后 POST submitUrl { answer: {...} }，并展示分数与解析。
 * 使用 Liquid Glass 设计：glass-card 容器、glass-light 选项、emerald 选中态。
 *
 * 提交格式契约：
 *   - multi     → { indices: [0, 1, 3] }
 *   - sort      → { order: [0, 3, 1, 2] }
 *   - match     → { pairs: [0, 1, 2, 3] }   // pairs[i] = 右列索引
 *   - branching → { choices: ["a", "x"], results: ["good"] }
 */
import { useState } from "react";
import { CheckCircle2, XCircle, Award, ArrowRight } from "lucide-react";

// ---------- 题型类型定义 ----------

interface MultiQuestion {
  type: "multi";
  question: string;
  options: string[];
  min_select?: number;
  max_select?: number;
}

interface SortQuestion {
  type: "sort";
  question: string;
  items: string[];
}

interface MatchQuestion {
  type: "match";
  question: string;
  left: string[];
  right: string[];
}

interface BranchOption {
  id: string;
  text: string;
  result?: "good" | "partial" | "bad";
  feedback?: string;
  sub_question?: {
    id: string;
    question: string;
    options: BranchOption[];
  };
}

interface BranchingQuestion {
  type: "branching";
  question: string;
  options: BranchOption[];
}

type Question =
  | MultiQuestion
  | SortQuestion
  | MatchQuestion
  | BranchingQuestion;

// ---------- 提交结果类型 ----------

interface SubmitResult {
  score: number;
  correct: boolean;
  explanation: string;
  details?: {
    label: string;
    is_correct: boolean;
    text: string;
  }[];
  xp_earned?: number;
}

interface Props {
  /** 题目对象（type 字段决定渲染哪种题型） */
  question: any;
  /** 提交 URL，POST { answer: {...} } */
  submitUrl: string;
  /** 完成后回调 */
  onClose?: () => void;
}

const TYPE_LABEL: Record<string, string> = {
  multi: "多选题",
  sort: "排序题",
  match: "匹配题",
  branching: "分支决策",
};

// ===================== 主组件 =====================

export function ScenarioQuestionRunner({ question, submitUrl, onClose }: Props) {
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const q = question as Question;

  // 统一提交函数：根据题型拼装 answer payload
  const submit = async (answer: unknown) => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(submitUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResult(data as SubmitResult);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "提交失败";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  // ----- 结果页 -----
  if (result) {
    return <ResultView result={result} onClose={onClose} />;
  }

  // ----- 答题页 -----
  return (
    <div className="glass-card specular-edge p-6 space-y-5">
      <header className="space-y-1">
        <span className="text-[10px] uppercase tracking-[0.15em] text-fg-dim">
          {TYPE_LABEL[q.type] || q.type}
        </span>
        <p className="text-sm font-semibold text-fg leading-relaxed">{q.question}</p>
      </header>

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
          {error}
        </div>
      )}

      {q.type === "multi" && (
        <MultiRunner
          q={q}
          submitting={submitting}
          onSubmit={(indices) => submit({ indices })}
        />
      )}
      {q.type === "sort" && (
        <SortRunner
          q={q}
          submitting={submitting}
          onSubmit={(order) => submit({ order })}
        />
      )}
      {q.type === "match" && (
        <MatchRunner
          q={q}
          submitting={submitting}
          onSubmit={(pairs) => submit({ pairs })}
        />
      )}
      {q.type === "branching" && (
        <BranchingRunner
          q={q}
          submitting={submitting}
          onSubmit={(choices, results) => submit({ choices, results })}
        />
      )}
    </div>
  );
}

// ===================== 多选题 =====================

function MultiRunner({
  q,
  submitting,
  onSubmit,
}: {
  q: MultiQuestion;
  submitting: boolean;
  onSubmit: (indices: number[]) => void;
}) {
  const [selected, setSelected] = useState<number[]>([]);

  const toggle = (i: number) => {
    if (selected.includes(i)) {
      setSelected(selected.filter((x) => x !== i));
    } else {
      const max = q.max_select ?? q.options.length;
      if (selected.length >= max) return;
      setSelected([...selected, i]);
    }
  };

  const minSelect = q.min_select ?? 1;
  const canSubmit = selected.length >= minSelect && !submitting;

  return (
    <div className="space-y-3">
      <div className="space-y-2">
        {q.options.map((opt, i) => {
          const isOn = selected.includes(i);
          return (
            <button
              key={i}
              type="button"
              onClick={() => toggle(i)}
              disabled={submitting}
              className={`w-full text-left px-4 py-3 rounded-[12px] text-sm transition-all duration-200 flex items-center gap-3 ${
                isOn
                  ? "border border-emerald-400/60 bg-emerald-500/15 text-fg"
                  : "glass-light text-fg-muted hover:text-fg hover:bg-white/[0.08]"
              }`}
            >
              <span
                className={`w-4 h-4 rounded-[5px] border flex items-center justify-center shrink-0 ${
                  isOn ? "border-emerald-400 bg-emerald-500" : "border-fg-dim/60"
                }`}
              >
                {isOn && <CheckCircle2 className="w-3 h-3 text-white" />}
              </span>
              <span>{opt}</span>
            </button>
          );
        })}
      </div>

      <div className="flex items-center justify-between text-xs text-fg-dim">
        <span>
          已选 {selected.length}/{q.options.length}
          {q.min_select ? `（至少 ${q.min_select}）` : ""}
        </span>
      </div>

      <button
        type="button"
        disabled={!canSubmit}
        onClick={() => onSubmit(selected)}
        className="glass-btn-primary w-full py-2.5 rounded-[12px] text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {submitting ? "提交中..." : "提交答案"}
      </button>
    </div>
  );
}

// ===================== 排序题 =====================

function SortRunner({
  q,
  submitting,
  onSubmit,
}: {
  q: SortQuestion;
  submitting: boolean;
  onSubmit: (order: number[]) => void;
}) {
  // order 数组：按点击顺序记录 items 的索引
  const [order, setOrder] = useState<number[]>([]);

  const toggle = (i: number) => {
    if (order.includes(i)) {
      setOrder(order.filter((x) => x !== i));
    } else {
      setOrder([...order, i]);
    }
  };

  const canSubmit = order.length === q.items.length && !submitting;
  const reset = () => setOrder([]);

  return (
    <div className="space-y-3">
      <p className="text-xs text-fg-muted">按正确顺序依次点击以下项目：</p>
      <div className="space-y-2">
        {q.items.map((item, i) => {
          const pos = order.indexOf(i);
          const isPicked = pos >= 0;
          return (
            <button
              key={i}
              type="button"
              onClick={() => toggle(i)}
              disabled={submitting}
              className={`w-full text-left px-4 py-3 rounded-[12px] text-sm transition-all duration-200 flex items-center gap-3 ${
                isPicked
                  ? "border border-emerald-400/60 bg-emerald-500/15 text-fg"
                  : "glass-light text-fg-muted hover:text-fg hover:bg-white/[0.08]"
              }`}
            >
              <span
                className={`w-6 h-6 shrink-0 rounded-full flex items-center justify-center text-xs font-semibold ${
                  isPicked
                    ? "bg-emerald-500 text-white"
                    : "border border-fg-dim/40 text-fg-dim"
                }`}
              >
                {isPicked ? pos + 1 : i + 1}
              </span>
              <span>{item}</span>
            </button>
          );
        })}
      </div>

      <div className="flex items-center justify-between text-xs text-fg-dim">
        <span>
          已排序 {order.length}/{q.items.length}
        </span>
        {order.length > 0 && (
          <button onClick={reset} className="hover:text-fg transition">
            重置
          </button>
        )}
      </div>

      <button
        type="button"
        disabled={!canSubmit}
        onClick={() => onSubmit(order)}
        className="glass-btn-primary w-full py-2.5 rounded-[12px] text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {submitting ? "提交中..." : "提交排序"}
      </button>
    </div>
  );
}

// ===================== 匹配题 =====================

function MatchRunner({
  q,
  submitting,
  onSubmit,
}: {
  q: MatchQuestion;
  submitting: boolean;
  onSubmit: (pairs: number[]) => void;
}) {
  // pairs[i] = j 表示左侧第 i 项与右侧第 j 项配对
  const [pairs, setPairs] = useState<(number | null)[]>(
    Array(q.left.length).fill(null)
  );
  const [activeLeft, setActiveLeft] = useState<number | null>(null);

  const clickLeft = (i: number) => {
    if (submitting) return;
    // 已配对的项再次点击会取消
    if (pairs[i] !== null) {
      setPairs(pairs.map((p, idx) => (idx === i ? null : p)));
      return;
    }
    setActiveLeft(i);
  };

  const clickRight = (j: number) => {
    if (submitting || activeLeft === null) return;
    // 移除其他项对 j 的占用
    const newPairs = pairs.map((p) => (p === j ? null : p));
    newPairs[activeLeft] = j;
    setPairs(newPairs);
    setActiveLeft(null);
  };

  const allMatched = pairs.every((p) => p !== null);

  return (
    <div className="space-y-3">
      <p className="text-xs text-fg-muted">
        先点击左侧条目（高亮），再点击右侧条目完成配对。
      </p>
      <div className="grid grid-cols-2 gap-3">
        {/* 左列 */}
        <div className="space-y-2">
          {q.left.map((item, i) => {
            const isActive = activeLeft === i;
            const matched = pairs[i] !== null;
            return (
              <button
                key={i}
                type="button"
                onClick={() => clickLeft(i)}
                disabled={submitting}
                className={`w-full text-left px-3 py-2.5 rounded-[12px] text-sm transition-all duration-200 ${
                  isActive
                    ? "border border-emerald-400 bg-emerald-500/20 text-fg"
                    : matched
                    ? "border border-emerald-400/50 bg-emerald-500/10 text-fg"
                    : "glass-light text-fg-muted hover:text-fg"
                }`}
              >
                <span className="text-fg-dim mr-2">{String.fromCharCode(65 + i)}.</span>
                {item}
              </button>
            );
          })}
        </div>
        {/* 右列 */}
        <div className="space-y-2">
          {q.right.map((item, j) => {
            const matchedBy = pairs.indexOf(j);
            const matched = matchedBy >= 0;
            return (
              <button
                key={j}
                type="button"
                onClick={() => clickRight(j)}
                disabled={submitting || activeLeft === null}
                className={`w-full text-left px-3 py-2.5 rounded-[12px] text-sm transition-all duration-200 ${
                  matched
                    ? "border border-emerald-400/50 bg-emerald-500/10 text-fg"
                    : activeLeft !== null
                    ? "glass-light text-fg hover:bg-white/[0.08] cursor-pointer"
                    : "glass-light text-fg-muted cursor-default"
                }`}
              >
                {matched && (
                  <span className="text-[10px] text-emerald-400 mr-2">
                    ← {String.fromCharCode(65 + matchedBy)}
                  </span>
                )}
                {item}
              </button>
            );
          })}
        </div>
      </div>

      <button
        type="button"
        disabled={!allMatched || submitting}
        onClick={() => onSubmit(pairs as number[])}
        className="glass-btn-primary w-full py-2.5 rounded-[12px] text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {submitting ? "提交中..." : "提交配对"}
      </button>
    </div>
  );
}

// ===================== 分支题 =====================

function BranchingRunner({
  q,
  submitting,
  onSubmit,
}: {
  q: BranchingQuestion;
  submitting: boolean;
  onSubmit: (choices: string[], results: string[]) => void;
}) {
  // 选择栈：每层是 { options, selectedId }
  const [stack, setStack] = useState<
    { options: BranchOption[]; selectedId: string | null }[]
  >([{ options: q.options, selectedId: null }]);

  const selectOption = (level: number, opt: BranchOption) => {
    if (submitting) return;
    // 截断 level 之后的所有层，再设置当前层
    const newStack = stack.slice(0, level + 1).map((l, idx) =>
      idx === level ? { ...l, selectedId: opt.id } : l
    );
    // 若有子问题，加入下一层
    if (opt.sub_question) {
      newStack.push({ options: opt.sub_question.options, selectedId: null });
    }
    setStack(newStack);
  };

  // 收集所有已选选项
  const collect = (): { choices: string[]; results: string[] } => {
    const choices: string[] = [];
    const results: string[] = [];
    for (const layer of stack) {
      if (!layer.selectedId) continue;
      const opt = layer.options.find((o) => o.id === layer.selectedId);
      if (!opt) continue;
      choices.push(opt.id);
      results.push(opt.result || "neutral");
    }
    return { choices, results };
  };

  // 所有层都已选择，且最后一层无子问题
  const allDone =
    stack.every((l) => l.selectedId !== null) &&
    (() => {
      const last = stack[stack.length - 1];
      if (!last.selectedId) return false;
      const opt = last.options.find((o) => o.id === last.selectedId);
      return !opt?.sub_question;
    })();

  const handleSubmit = () => {
    const { choices, results } = collect();
    onSubmit(choices, results);
  };

  return (
    <div className="space-y-4">
      {stack.map((layer, level) => {
        const selectedOpt = layer.options.find((o) => o.id === layer.selectedId);
        return (
          <div key={level} className="space-y-2">
            {level > 0 && (
              <p className="text-[10px] uppercase tracking-[0.15em] text-fg-dim">
                子问题 {level + 1}
              </p>
            )}
            <div className="space-y-2">
              {layer.options.map((opt) => {
                const isSel = layer.selectedId === opt.id;
                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => selectOption(level, opt)}
                    disabled={submitting}
                    className={`w-full text-left px-4 py-3 rounded-[12px] text-sm transition-all duration-200 flex items-center gap-3 ${
                      isSel
                        ? "border border-emerald-400/60 bg-emerald-500/15 text-fg"
                        : "glass-light text-fg-muted hover:text-fg hover:bg-white/[0.08]"
                    }`}
                  >
                    <span className="w-5 text-center text-xs font-mono text-fg-dim">
                      {opt.id.toUpperCase()}
                    </span>
                    <span>{opt.text}</span>
                  </button>
                );
              })}
            </div>
            {selectedOpt?.feedback && (
              <div className="ml-2 text-xs text-fg-muted">
                <ArrowRight className="w-3 h-3 inline mr-1 text-emerald-400" />
                {selectedOpt.feedback}
              </div>
            )}
          </div>
        );
      })}

      <button
        type="button"
        disabled={!allDone || submitting}
        onClick={handleSubmit}
        className="glass-btn-primary w-full py-2.5 rounded-[12px] text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {submitting ? "提交中..." : "提交决策"}
      </button>
    </div>
  );
}

// ===================== 结果展示 =====================

function ResultView({
  result,
  onClose,
}: {
  result: SubmitResult;
  onClose?: () => void;
}) {
  return (
    <div className="glass-card specular-edge p-6 space-y-4">
      {/* 分数与图标 */}
      <div className="text-center space-y-2 py-2">
        <div
          className={`w-16 h-16 mx-auto rounded-full flex items-center justify-center ${
            result.correct ? "bg-emerald-500/15" : "bg-rose-500/15"
          }`}
        >
          <Award
            className={`w-8 h-8 ${
              result.correct ? "text-emerald-400" : "text-rose-400"
            }`}
          />
        </div>
        <p
          className={`text-3xl font-bold ${
            result.correct ? "text-emerald-400" : "text-rose-400"
          }`}
        >
          {result.score} 分
        </p>
        {(result.xp_earned ?? 0) > 0 && (
          <p className="text-xs text-amber-400">+{result.xp_earned} XP</p>
        )}
      </div>

      {/* 解析 */}
      {result.explanation && (
        <div className="glass-light rounded-[12px] p-3 text-sm text-fg-muted leading-relaxed">
          <p className="text-xs text-fg-dim uppercase tracking-wider mb-1">解析</p>
          {result.explanation}
        </div>
      )}

      {/* 详细条目 */}
      {result.details && result.details.length > 0 && (
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {result.details.map((d, i) => (
            <div
              key={i}
              className={`glass-light rounded-[12px] p-3 text-xs ${
                d.is_correct ? "" : "border-rose-400/20"
              }`}
            >
              <div className="flex items-start gap-2">
                {d.is_correct ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                )}
                <div className="space-y-0.5">
                  <p className="text-fg font-medium">{d.label}</p>
                  <p className="text-fg-dim">{d.text}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="glass-btn-primary w-full py-2.5 rounded-[12px] text-sm font-semibold"
        >
          完成
        </button>
      )}
    </div>
  );
}
