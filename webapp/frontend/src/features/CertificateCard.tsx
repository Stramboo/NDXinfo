/**
 * CertificateCard.tsx — 结业证书墙 (v2.4 Phase 5)
 */
import { useEffect, useState } from "react";
import { GraduationCap } from "lucide-react";

interface Certificate {
  stage_id: string;
  title: string;
  score: number;
  passed_at: string;
}

export function CertificateWall() {
  const [certs, setCerts] = useState<Certificate[]>([]);

  useEffect(() => {
    fetch("/api/learning/certificates")
      .then((r) => r.json())
      .then(setCerts)
      .catch(() => {});
  }, []);

  if (certs.length === 0) return null;

  return (
    <div className="space-y-3">
      <p className="text-xs text-fg-muted uppercase tracking-wider">结业证书</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {certs.map((c) => (
          <div key={c.stage_id}
               className="glass-card specular-edge p-4 relative overflow-hidden">
            {/* 背景光晕 */}
            <div className="absolute -top-8 -right-8 w-24 h-24 rounded-full
                            bg-emerald-500/10 blur-2xl pointer-events-none" />
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-[12px] bg-gradient-to-br from-emerald-400/20 to-emerald-600/10
                              border border-emerald-400/30 flex items-center justify-center shrink-0">
                <GraduationCap className="w-5 h-5 text-emerald-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-fg truncate">{c.title}</p>
                <p className="text-xs text-fg-dim mt-0.5">
                  成绩 {c.score} 分 · {new Date(c.passed_at).toLocaleDateString()}
                </p>
              </div>
              <span className="text-emerald-400 text-lg">🏅</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
