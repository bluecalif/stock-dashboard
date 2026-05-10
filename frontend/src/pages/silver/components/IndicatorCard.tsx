type IndicatorStatus =
  | "과매수"
  | "과매도"
  | "중립"
  | "골든크로스"
  | "데드크로스"
  | "고변동"
  | "저변동";

type Indicator = {
  name: string;
  value: number;
  unit?: string;
  status: IndicatorStatus;
};

type Props = {
  assetLabel: string;
  indicators: Indicator[];
};

const STATUS_COLOR: Record<IndicatorStatus, string> = {
  과매수: "var(--accent-red)",
  과매도: "var(--accent-green)",
  중립: "var(--text-secondary)",
  골든크로스: "var(--accent-green)",
  데드크로스: "var(--accent-red)",
  고변동: "var(--accent-amber)",
  저변동: "var(--text-secondary)",
};

export default function IndicatorCard({ assetLabel, indicators }: Props) {
  return (
    <div className="silver-card">
      <div
        style={{
          fontSize: 12,
          color: "var(--text-secondary)",
          textTransform: "uppercase",
          letterSpacing: "0.04em",
          fontWeight: 500,
          marginBottom: 14,
        }}
      >
        현재 지표 — {assetLabel}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {indicators.map((ind) => (
          <div
            key={ind.name}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              paddingBottom: 12,
              borderBottom: "1px solid var(--border-subtle)",
            }}
          >
            <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>{ind.name}</span>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span
                style={{
                  fontSize: 15,
                  fontWeight: 600,
                  fontVariantNumeric: "tabular-nums",
                  color: "var(--text-primary)",
                }}
              >
                {ind.value.toFixed(2)}
                {ind.unit && (
                  <span style={{ fontSize: 12, color: "var(--text-secondary)", marginLeft: 2 }}>
                    {ind.unit}
                  </span>
                )}
              </span>
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: STATUS_COLOR[ind.status],
                  padding: "2px 8px",
                  borderRadius: 4,
                  background: `${STATUS_COLOR[ind.status]}18`,
                }}
              >
                {ind.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
