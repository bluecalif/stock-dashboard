type Props = {
  label: string;
  value: string;
  delta?: number;
  sub?: string;
};

export default function KpiCard({ label, value, delta, sub }: Props) {
  const tone =
    delta === undefined ? "" : delta >= 0 ? " silver-kpi-card__value--positive" : " silver-kpi-card__value--negative";

  return (
    <div className="silver-kpi-card">
      <div className="silver-kpi-card__label">{label}</div>
      <div className={`silver-kpi-card__value${tone}`}>{value}</div>
      {sub && <div className="silver-kpi-card__footer">{sub}</div>}
    </div>
  );
}
