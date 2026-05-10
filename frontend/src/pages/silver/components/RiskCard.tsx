import type { SimKpi } from "../../../types/api";
import { formatPct } from "../silverUtils";

type Props = {
  assetLabel: string;
  kpi: SimKpi;
};

export default function RiskCard({ assetLabel, kpi }: Props) {
  const mdd = kpi.yearly_worst_mdd;
  const pct = Math.abs(mdd * 100).toFixed(1);

  return (
    <div className="silver-risk-card">
      <div
        style={{
          fontSize: 12,
          color: "#F59E0B",
          textTransform: "uppercase",
          letterSpacing: "0.04em",
          fontWeight: 500,
          marginBottom: 8,
        }}
      >
        ⚠ 리스크 — {assetLabel}
      </div>
      <div
        style={{
          fontSize: 28,
          fontWeight: 700,
          color: "var(--accent-amber)",
          fontVariantNumeric: "tabular-nums",
          letterSpacing: "-0.02em",
          marginBottom: 6,
        }}
      >
        {formatPct(mdd)}
      </div>
      <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: 0, lineHeight: 1.6 }}>
        시뮬레이션 기간 중 한 해에 최대 <strong style={{ color: "#F59E0B" }}>{pct}%</strong>까지
        적립 자산 평가액이 하락한 적이 있습니다. 장기 적립의 경우 이런 구간도 인내하는 것이 핵심입니다.
      </p>
    </div>
  );
}
