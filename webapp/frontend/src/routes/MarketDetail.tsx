/**
 * MarketDetail.tsx — 市场详情页 (Phase 3)
 *
 * 展示单个市场的完整信息：交易所、指数、货币、代表公司、行业分布。
 */
import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";

interface MarketDetail {
  id: string;
  name: string;
  fullName: string;
  exchanges: string[];
  currency: string;
  currencySymbol: string;
  indices: { name: string; symbol: string; description: string }[];
  features: string[];
  description: string;
  localTimes: { open: string; close: string };
  status: { isOpen: boolean; status: string };
  companies: Company[];
  companyCount: number;
}

interface Company {
  symbol: string;
  name: string;
  nameEn: string;
  market: string;
  sector: string;
  industry: string;
  products: string;
  description: string;
}

const SECTOR_COLORS: Record<string, string> = {
  "科技": "bg-blue-500/10 text-blue-400 border-blue-500/20",
  "金融": "bg-amber-500/10 text-amber-400 border-amber-500/20",
  "消费": "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  "医药": "bg-rose-500/10 text-rose-400 border-rose-500/20",
  "能源": "bg-orange-500/10 text-orange-400 border-orange-500/20",
  "工业": "bg-slate-500/10 text-slate-400 border-slate-500/20",
};

const STATUS_LABELS: Record<string, string> = {
  open: "正在交易", scheduled: "即将开盘", closed: "已收盘", unknown: "休市",
};

export function MarketDetail() {
  const { marketId } = useParams<{ marketId: string }>();
  const [data, setData] = useState<MarketDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!marketId) return;
    fetch(`/api/explore/markets/${marketId}`)
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [marketId]);

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto py-8 px-4 space-y-6">
        <div className="h-5 w-24 rounded bg-bg-subtle animate-pulse" />
        <div className="h-8 w-48 rounded bg-bg-subtle animate-pulse" />
        <div className="grid grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-bg-panel animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="max-w-3xl mx-auto py-8 px-4 text-center text-fg-dim">
        <p>该市场信息暂无数据。</p>
        <Link to="/explore" className="text-emerald-400 hover:underline text-sm mt-2 inline-block">
          ← 返回世界市场
        </Link>
      </div>
    );
  }

  const sectorGroups = data.companies.reduce<Record<string, Company[]>>((acc, c) => {
    (acc[c.sector] ||= []).push(c);
    return acc;
  }, {});

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 space-y-8">
      {/* 返回链接 */}
      <Link to="/explore" className="text-xs text-fg-dim hover:text-fg transition inline-flex items-center gap-1">
        ← 返回世界市场
      </Link>

      {/* 标题区域 */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-fg">{data.name}</h1>
          {data.status.isOpen ? (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              {STATUS_LABELS[data.status.status]}
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded bg-bg-subtle text-fg-dim text-xs">
              {STATUS_LABELS[data.status.status]}
            </span>
          )}
        </div>
        <p className="text-sm text-fg-muted leading-relaxed">{data.description}</p>
      </div>

      {/* 关键信息卡片 */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "交易所", value: data.exchanges[0] },
          { label: "交易货币", value: `${data.currencySymbol} ${data.currency}` },
          { label: "北京时间", value: `${data.localTimes.open} - ${data.localTimes.close}` },
          { label: "上市公司", value: `${data.companyCount}+ 家` },
        ].map((item) => (
          <div key={item.label} className="rounded-xl bg-bg-panel border border-line p-3">
            <p className="text-[10px] text-fg-muted uppercase tracking-wider">{item.label}</p>
            <p className="text-sm font-semibold text-fg mt-1">{item.value}</p>
          </div>
        ))}
      </div>

      {/* 代表指数 */}
      <div className="rounded-xl bg-bg-panel border border-line p-5 space-y-3">
        <p className="text-xs text-fg-muted uppercase tracking-wider">代表指数</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {data.indices.map((ix) => (
            <div key={ix.symbol} className="rounded-lg bg-bg-subtle p-3">
              <p className="text-sm font-semibold text-fg">{ix.name}</p>
              <p className="text-[10px] text-fg-dim mt-0.5">{ix.description}</p>
              <p className="text-[10px] text-fg-muted mt-1 font-mono">{ix.symbol}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 市场特点 */}
      <div className="rounded-xl bg-bg-panel border border-line p-5 space-y-2">
        <p className="text-xs text-fg-muted uppercase tracking-wider">市场特点</p>
        <ul className="space-y-1.5">
          {data.features.map((f, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-fg">
              <span className="text-emerald-400 mt-0.5">•</span>
              {f}
            </li>
          ))}
        </ul>
      </div>

      {/* 代表公司（按行业分组） */}
      <div className="space-y-4">
        <p className="text-xs text-fg-muted uppercase tracking-wider">
          代表公司（{data.companyCount} 家）
        </p>
        {Object.entries(sectorGroups).map(([sector, companies]) => (
          <div key={sector} className="space-y-2">
            <p className="text-xs font-semibold text-fg-dim">{sector}</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {companies.map((c) => (
                <div
                  key={c.symbol}
                  className="flex items-start gap-3 rounded-lg bg-bg-panel border border-line p-3
                             hover:border-emerald-500/20 transition"
                >
                  <span
                    className={`shrink-0 w-7 h-7 rounded-md flex items-center justify-center text-[10px] font-bold border ${
                      SECTOR_COLORS[c.sector] || "bg-bg-subtle text-fg-dim border-line"
                    }`}
                  >
                    {c.name.charAt(0)}
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-fg truncate">
                      {c.name}
                    </p>
                    <p className="text-[10px] text-fg-dim">{c.symbol} · {c.industry}</p>
                    <p className="text-[10px] text-fg-muted mt-0.5 line-clamp-1">
                      {c.description || c.products}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
