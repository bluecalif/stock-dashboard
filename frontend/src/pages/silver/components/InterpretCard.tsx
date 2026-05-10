import type { SimKpi } from "../../../types/api";
import { formatKRW, formatPct } from "../silverUtils";

type Props = {
  assetLabel: string;
  periodYears: number;
  monthlyAmount: number;
  kpi: SimKpi;
};

export default function InterpretCard({
  assetLabel,
  periodYears,
  monthlyAmount,
  kpi,
}: Props) {
  const totalDeposit = kpi.total_deposit_krw;
  const gain = kpi.final_asset_krw - totalDeposit;
  const isPositive = gain >= 0;

  return (
    <div className="silver-card" style={{ lineHeight: 1.7 }}>
      <div
        style={{
          fontSize: 12,
          color: "var(--text-secondary)",
          textTransform: "uppercase",
          letterSpacing: "0.04em",
          marginBottom: 10,
          fontWeight: 500,
        }}
      >
        한 줄 해석 — {assetLabel}
      </div>
      <p style={{ fontSize: 14, color: "var(--text-primary)", margin: 0 }}>
        {periodYears}년간 매월 <strong style={{ color: "var(--text-primary)" }}>{formatKRW(monthlyAmount)}</strong>씩{" "}
        <strong style={{ color: "var(--accent-blue)" }}>{assetLabel}</strong>에 적립했다면,
        총 원금 {formatKRW(totalDeposit)}이{" "}
        <strong style={{ color: isPositive ? "var(--accent-green)" : "var(--accent-red)" }}>
          {formatKRW(kpi.final_asset_krw)}
        </strong>
        이 되어{" "}
        <span style={{ color: isPositive ? "var(--accent-green)" : "var(--accent-red)" }}>
          {isPositive ? `약 ${formatKRW(gain)}을 번` : `약 ${formatKRW(Math.abs(gain))}을 잃은`}
        </span>{" "}
        결과입니다. 연환산 수익률은{" "}
        <strong style={{ color: kpi.annualized_return >= 0 ? "var(--accent-green)" : "var(--accent-red)" }}>
          {formatPct(kpi.annualized_return)}
        </strong>
        입니다.
      </p>
    </div>
  );
}
