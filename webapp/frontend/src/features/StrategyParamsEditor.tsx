/**
 * StrategyParamsEditor -- 策略参数编辑器
 *
 * 从后端 GET /api/strategy/{name}/params 读取当前策略参数，
 * 提供 slider / number input 编辑，通过 PUT 保存到后端。
 */

import { useEffect, useState, useCallback } from "react";
import { Save, RefreshCw, AlertCircle, Check, Settings2 } from "lucide-react";
import { api } from "../lib/api";

type ParamValue = number | string | boolean;
type ParamsMap = Record<string, ParamValue>;

interface Props {
  strategyName: string;
}

export function StrategyParamsEditor({ strategyName }: Props) {
  const [params, setParams] = useState<ParamsMap | null>(null);
  const [edited, setEdited] = useState<ParamsMap>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ---- 加载 ----

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const p = await api.strategyParams(strategyName);
      setParams(p);
      setEdited({ ...p });
    } catch (e: any) {
      setError(e?.message || "加载参数失败");
    } finally {
      setLoading(false);
    }
  }, [strategyName]);

  useEffect(() => { load(); }, [load]);

  // ---- 变更 ----

  const changeParam = (key: string, value: ParamValue) => {
    setEdited(prev => ({ ...prev, [key]: value }));
    setMsg(null);
  };

  const undoParam = (key: string) => {
    if (!params) return;
    setEdited(prev => ({ ...prev, [key]: params[key] }));
  };

  const isDirty = (key: string) => {
    if (!params) return false;
    return JSON.stringify(edited[key]) !== JSON.stringify(params[key]);
  };

  // ---- 保存 ----

  const save = async () => {
    setSaving(true);
    setMsg(null);
    setError(null);
    try {
      const result = await api.updateStrategyParams(strategyName, edited);
      setParams({ ...edited, ...result });
      setMsg({ ok: true, text: "参数已保存" });
    } catch (e: any) {
      setMsg({ ok: false, text: e?.message || "保存失败" });
    } finally {
      setSaving(false);
    }
  };

  // ---- 参数类型判断 ----

  const guessFieldType = (key: string, val: ParamValue): "pct" | "number" | "bool" | "text" => {
    if (typeof val === "boolean") return "bool";
    if (typeof val === "string") return "text";

    // 按 key 名推断百分比
    if (/pct|ratio|weight|rate/i.test(key) && val >= 0 && val <= 1) return "pct";
    if (/pct/i.test(key) && val > 1) return "pct"; // 后端可能存 5 表示 5%

    return "number";
  };

  const formatValue = (val: ParamValue, type: ReturnType<typeof guessFieldType>): string => {
    if (typeof val === "boolean") return val ? "是" : "否";
    if (typeof val === "string") return val;
    if (type === "pct") {
      // 0-1 range => display as %
      if (val >= 0 && val <= 1) return `${(val * 100).toFixed(1)}%`;
      return `${val}%`;
    }
    if (Number.isInteger(val)) return String(val);
    return val.toFixed(4);
  };

  // ---- 渲染 ----

  if (loading) {
    return (
      <div className="panel-card p-5">
        <h2 className="flex items-center gap-2 text-fg text-lg font-semibold mb-4">
          <Settings2 className="h-5 w-5" />
          策略参数
        </h2>
        <p className="text-fg-muted text-sm">加载中…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="panel-card p-5">
        <h2 className="flex items-center gap-2 text-fg text-lg font-semibold mb-4">
          <Settings2 className="h-5 w-5" />
          策略参数
        </h2>
        <div className="px-3 py-2 bg-neg rounded-lg text-rose-400 text-sm flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          {error}
          <button onClick={load} className="ml-auto text-xs underline">重试</button>
        </div>
      </div>
    );
  }

  if (!params || Object.keys(params).length === 0) {
    return (
      <div className="panel-card p-5">
        <h2 className="flex items-center gap-2 text-fg text-lg font-semibold mb-4">
          <Settings2 className="h-5 w-5" />
          策略参数
        </h2>
        <p className="text-fg-muted text-sm">当前策略无可配置参数。</p>
      </div>
    );
  }

  const entries = Object.entries(edited);
  const dirtyCount = Object.keys(params).filter(isDirty).length;

  return (
    <div className="panel-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="flex items-center gap-2 text-fg text-lg font-semibold">
          <Settings2 className="h-5 w-5" />
          策略参数
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={load}
            className="p-1.5 rounded text-fg-muted hover:text-fg hover:bg-bg-hover transition"
            title="刷新"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* 消息 */}
      {msg && (
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm mb-4 ${
          msg.ok ? "bg-pos text-emerald-400" : "bg-neg text-rose-400"
        }`}>
          {msg.ok ? <Check className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
          {msg.text}
        </div>
      )}

      {/* 参数字段 */}
      <div className="space-y-4">
        {entries.map(([key, val]) => {
          const type = guessFieldType(key, val);
          const dirty = isDirty(key);
          const paramKey = `${strategyName}-${key}`;

          return (
            <div key={key} className={`rounded-lg p-3 transition ${
              dirty ? "bg-emerald-500/5 border border-emerald-500/30" : "bg-bg-subtle"
            }`}>
              <div className="flex items-center justify-between mb-2">
                <label
                  htmlFor={paramKey}
                  className="text-[10px] uppercase tracking-wider text-fg-muted"
                >
                  {key.replace(/_/g, " ")}
                </label>
                <div className="flex items-center gap-1.5">
                  {dirty && (
                    <span className="text-[10px] text-emerald-400">已修改</span>
                  )}
                  {dirty && (
                    <button
                      onClick={() => undoParam(key)}
                      className="text-[10px] text-fg-muted hover:text-fg underline"
                    >
                      撤销
                    </button>
                  )}
                  <span className="tabular text-xs text-fg-dim">
                    {formatValue(val, type)}
                  </span>
                </div>
              </div>

              {/* 布尔参数 */}
              {type === "bool" && (
                <button
                  onClick={() => changeParam(key, !val)}
                  className={`px-3 py-1.5 rounded-lg text-sm transition border ${
                    val
                      ? "bg-emerald-500/10 border-emerald-500 text-emerald-400"
                      : "bg-bg-input border-line text-fg-muted"
                  }`}
                >
                  {val ? "已启用" : "关闭"}
                </button>
              )}

              {/* 字符串参数 */}
              {type === "text" && (
                <input
                  id={paramKey}
                  type="text"
                  value={val as string}
                  onChange={e => changeParam(key, e.target.value)}
                  className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-sm text-fg focus:outline-none focus:border-emerald-500"
                />
              )}

              {/* 百分比参数 */}
              {type === "pct" && typeof val === "number" && (
                <div className="flex items-center gap-3">
                  <input
                    id={paramKey}
                    type="range"
                    min={0}
                    max={val >= 0 && val <= 1 ? 1 : 100}
                    step={val >= 0 && val <= 1 ? 0.01 : 0.5}
                    value={val}
                    onChange={e => changeParam(key, Number(e.target.value))}
                    className="flex-1 h-1.5 rounded-full appearance-none bg-bg-input cursor-pointer
                               [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-4
                               [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:rounded-full
                               [&::-webkit-slider-thumb]:bg-emerald-500 [&::-webkit-slider-thumb]:cursor-pointer"
                  />
                  <input
                    type="number"
                    step={val >= 0 && val <= 1 ? 0.01 : 0.5}
                    value={val}
                    onChange={e => changeParam(key, Number(e.target.value))}
                    className="w-20 bg-bg-input border border-line rounded-lg px-2 py-1.5 text-sm text-fg tabular text-right focus:outline-none focus:border-emerald-500"
                  />
                </div>
              )}

              {/* 普通数字参数 */}
              {type === "number" && typeof val === "number" && (
                <input
                  id={paramKey}
                  type="number"
                  step="any"
                  value={val}
                  onChange={e => changeParam(key, Number(e.target.value))}
                  className="w-full bg-bg-input border border-line rounded-lg px-3 py-2 text-sm text-fg tabular focus:outline-none focus:border-emerald-500"
                />
              )}
            </div>
          );
        })}
      </div>

      {/* 保存按钮 */}
      <div className="mt-5 pt-4 border-t border-line flex items-center justify-between">
        <div className="text-xs text-fg-muted">
          {dirtyCount > 0
            ? `${dirtyCount} 个参数已修改`
            : "所有参数已保存"}
        </div>
        <button
          onClick={save}
          disabled={dirtyCount === 0 || saving}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-emerald-500 text-bg hover:bg-emerald-600 transition disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {saving ? (
            <span className="inline-block w-3.5 h-3.5 border-2 border-bg border-t-transparent rounded-full animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          {saving ? "保存中…" : "保存参数"}
        </button>
      </div>
    </div>
  );
}
