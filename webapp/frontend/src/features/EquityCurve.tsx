/**
 * EquityCurve — 用纯 SVG 画 1 根平滑曲线 + 面积渐变
 *   不引第三方图表库，让首屏更小
 */

import { useTradeStore } from "../store/tradeStore";
import { fmtMoney, fmtPct } from "../lib/utils";

export function EquityCurve() {
  const data = useTradeStore((s) => s.equityHistory);

  if (data.length < 2) {
    return (
      <div className="h-64 grid place-items-center text-fg-muted text-sm">
        暂未收集到足够 tick，点几下 Trading 页面下单试试？
      </div>
    );
  }

  const W = 1000;
  const H = 240;
  const PAD = 32;

  const xs = data.map((d) => d.ts);
  const ys = data.map((d) => d.equity);
  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  const yMin = Math.min(...ys);
  const yMax = Math.max(...ys);
  const yRange = Math.max(1, yMax - yMin);

  const toX = (x: number) => PAD + ((x - xMin) / (xMax - xMin || 1)) * (W - 2 * PAD);
  const toY = (y: number) => H - PAD - ((y - yMin) / yRange) * (H - 2 * PAD);

  // 平滑路径（Catmull-Rom → Bezier）
  const pts = data.map((d, i) => [toX(d.ts), toY(d.equity)] as [number, number]);
  let pathD = `M ${pts[0][0]} ${pts[0][1]}`;
  for (let i = 1; i < pts.length; i++) {
    const prev = pts[i - 1];
    const curr = pts[i];
    const cx1 = prev[0] + (curr[0] - prev[0]) / 2;
    const cy1 = prev[1];
    const cx2 = prev[0] + (curr[0] - prev[0]) / 2;
    const cy2 = curr[1];
    pathD += ` C ${cx1} ${cy1}, ${cx2} ${cy2}, ${curr[0]} ${curr[1]}`;
  }

  // 面积
  const areaD =
    pathD +
    ` L ${pts[pts.length - 1][0]} ${H - PAD} L ${pts[0][0]} ${H - PAD} Z`;

  const first = data[0].equity;
  const last = data[data.length - 1].equity;
  const diff = last - first;
  const diffPct = first === 0 ? 0 : (last / first - 1) * 100;
  const positive = diff >= 0;
  const stroke = positive ? "#10B981" : "#F43F5E";
  const fill   = positive ? "url(#g-pos)" : "url(#g-neg)";

  return (
    <div className="w-full">
      <div className="flex items-end justify-between mb-2">
        <div>
          <div className="text-2xl font-bold tabular text-fg">
            ${fmtMoney(last)}
          </div>
          <div className={`tabular text-sm mt-1 ${positive ? "text-emerald-400" : "text-rose-400"}`}>
            {positive ? "▲" : "▼"} ${fmtMoney(Math.abs(diff))} ({fmtPct(diffPct)})
          </div>
        </div>
        <div className="text-xs text-fg-muted tabular">
          {data.length} points · {new Date(data[0].ts).toLocaleTimeString("zh-CN")}
          {" → "}
          {new Date(data[data.length - 1].ts).toLocaleTimeString("zh-CN")}
        </div>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-64" preserveAspectRatio="none">
        <defs>
          <linearGradient id="g-pos" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#10B981" stopOpacity="0.32" />
            <stop offset="100%" stopColor="#10B981" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="g-neg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#F43F5E" stopOpacity="0.32" />
            <stop offset="100%" stopColor="#F43F5E" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* 网格 */}
        {[0.25, 0.5, 0.75].map((p) => (
          <line key={p} x1={PAD} x2={W - PAD} y1={H * p} y2={H * p}
                stroke="#1F222C" strokeDasharray="2 4" />
        ))}

        {/* 面积 + 曲线 */}
        <path d={areaD} fill={fill} />
        <path d={pathD} fill="none" stroke={stroke} strokeWidth={2} />

        {/* 端点 */}
        <circle cx={pts[pts.length - 1][0]} cy={pts[pts.length - 1][1]}
                r="3" fill={stroke} />
      </svg>
    </div>
  );
}
