/**
 * Explore.tsx — 世界市场探索 (Phase 3)
 *
 * 展示全球 8 大股票市场，动态交易时间轴，市场入口卡片。
 */
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";

interface Market {
  id: string;
  name: string;
  fullName: string;
  exchanges: string[];
  currency: string;
  currencySymbol: string;
  indices: { name: string; symbol: string; description: string }[];
  features: string[];
  description: string;
  status: { isOpen: boolean; status: string };
}

const STATUS_LABELS: Record<string, string> = {
  open: "交易中",
  scheduled: "即将开盘",
  closed: "已收盘",
  closed_weekend: "周末休市",
  unknown: "-",
};
const STATUS_COLORS: Record<string, string> = {
  open: "text-emerald-400 bg-emerald-500/10",
  scheduled: "text-amber-400 bg-amber-500/10",
  closed: "text-fg-dim bg-bg-subtle",
  closed_weekend: "text-fg-dim bg-bg-subtle",
  unknown: "text-fg-dim bg-bg-subtle",
};

export function Explore() {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/explore/markets")
      .then((r) => r.json())
      .then((data) => {
        setMarkets(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // 按地理分区
  const asianMarkets = markets.filter((m) => ["cn", "hk", "jp", "kr"].includes(m.id));
  const euMarkets = markets.filter((m) => ["uk", "de"].includes(m.id));
  const naMarkets = markets.filter((m) => ["us", "ca"].includes(m.id));

  const regionCards = [
    { label: "亚洲", markets: asianMarkets, bg: "from-amber-500/5 to-rose-500/5" },
    { label: "欧洲", markets: euMarkets, bg: "from-blue-500/5 to-indigo-500/5" },
    { label: "北美", markets: naMarkets, bg: "from-emerald-500/5 to-teal-500/5" },
  ];

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-8">
      {/* 头部 */}
      <div className="space-y-2">
        <p className="text-xs text-fg-muted uppercase tracking-wider">世界市场</p>
        <h1 className="text-2xl font-bold text-fg">全球股票市场</h1>
        <p className="text-sm text-fg-muted leading-relaxed max-w-lg">
          从纽约到东京，每家上市公司都在某个交易所挂牌交易。了解不同市场的规则和节奏，是成为成熟投资者的第一步。
        </p>
      </div>

      {/* 动态时间轴 */}
      <div className="glass-card p-5 space-y-3">
        <p className="text-xs text-fg-muted uppercase tracking-wider">全球交易时段</p>
        {loading ? (
          <div className="flex gap-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-8 w-24 glass-light rounded-[12px] animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-2 text-sm">
            {markets.map((m) => (
              <span
                key={m.id}
                className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs ${
                  STATUS_COLORS[m.status?.status] || STATUS_COLORS.unknown
                }`}
              >
                {m.name.split(" ")[1] || m.name} ·{" "}
                {STATUS_LABELS[m.status?.status] || "-"}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 按区域分组 */}
      {loading ? (
        <div className="space-y-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="space-y-3">
              <div className="h-5 w-16 rounded bg-bg-subtle animate-pulse" />
              <div className="grid grid-cols-2 gap-3">
                {[1, 2].map((j) => (
                  <div key={j} className="h-32 rounded-xl bg-bg-panel animate-pulse" />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-8">
          {regionCards.map((region) => (
            <div key={region.label} className="space-y-3">
              <h2 className="text-sm font-semibold text-fg-muted">{region.label}</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {region.markets.map((m) => (
                  <Link
                    key={m.id}
                    to={`/explore/markets/${m.id}`}
                    className="block glass-card p-4
                               hover:border-emerald-500/30 hover:bg-bg-subtle transition-all group"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{m.name.split(" ")[1]}</span>
                        <span
                          className={`inline-block w-2 h-2 rounded-full ${
                            m.status?.isOpen ? "bg-emerald-400 animate-pulse" : "bg-fg-dim"
                          }`}
                        />
                      </div>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded ${
                          STATUS_COLORS[m.status?.status] || STATUS_COLORS.unknown
                        }`}
                      >
                        {STATUS_LABELS[m.status?.status] || "-"}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-fg group-hover:text-emerald-400 transition">
                      {m.name.replace(/[^\u4e00-\u9fff]/g, "").replace(/\s/g, "")} — {m.currencySymbol}
                      {m.currency}
                    </p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {m.indices.map((ix) => (
                        <span key={ix.symbol} className="text-[10px] px-1.5 py-0.5 rounded bg-bg-subtle text-fg-dim">
                          {ix.name}
                        </span>
                      ))}
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 探索方式 */}
      <div className="rounded-xl bg-gradient-to-br from-emerald-500/5 to-teal-500/5 border border-line p-5 space-y-3">
        <p className="text-xs text-fg-muted uppercase tracking-wider">按你的方式探索</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            { icon: "🏢", label: "按行业", desc: "科技 / 金融 / 医疗 / 消费", to: "/explore" },
            { icon: "🌍", label: "按市场", desc: "美国 / 中国 / 日本 / 欧洲", to: "/explore" },
            { icon: "📱", label: "按产品", desc: "手机 / 汽车 / 软件 / 芯片", to: "/explore" },
          ].map((item) => (
            <Link
              key={item.label}
              to={item.to}
              className="flex items-center gap-3 rounded-lg p-3 bg-bg-panel/50 hover:bg-bg-panel transition"
            >
              <span className="text-xl">{item.icon}</span>
              <div>
                <p className="text-xs font-semibold text-fg">{item.label}</p>
                <p className="text-[10px] text-fg-dim">{item.desc}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
