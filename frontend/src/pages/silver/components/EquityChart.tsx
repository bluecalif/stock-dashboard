import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
  Legend,
} from "recharts";
import type { ChartRow } from "../silverUtils";

export const SERIES_COLORS = [
  "#3DD68C",
  "#60A5FA",
  "#A78BFA",
  "#F59E0B",
  "#EF4444",
  "#94A3B8",
];

export type SeriesDef = { key: string; label: string };

type Props = {
  data: ChartRow[];
  series: SeriesDef[];
  paddingStart?: string;
  height?: number;
  className?: string;
};

function yFormatter(v: number): string {
  if (v >= 100_000_000) return `${(v / 100_000_000).toFixed(0)}억`;
  if (v >= 10_000) return `${(v / 10_000).toFixed(0)}만`;
  return String(v);
}

function tooltipFormatter(value: number | string): string {
  if (typeof value !== "number") return String(value);
  if (value >= 100_000_000) return `${(value / 100_000_000).toFixed(2)}억원`;
  if (value >= 10_000) return `${(value / 10_000).toFixed(0)}만원`;
  return `${value.toLocaleString("ko-KR")}원`;
}

export default function EquityChart({
  data,
  series,
  paddingStart,
  height,
  className,
}: Props) {
  return (
    <div
      className={`silver-equity-chart-wrap${className ? ` ${className}` : ""}`}
      style={height !== undefined ? { height } : undefined}
    >
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 16, right: 16, bottom: 8, left: 8 }}>
        <defs>
          {series.map((s, i) => (
            <linearGradient key={s.key} id={`grad-${s.key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={SERIES_COLORS[i % SERIES_COLORS.length]} stopOpacity={0.32} />
              <stop offset="100%" stopColor={SERIES_COLORS[i % SERIES_COLORS.length]} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>

        <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />

        <XAxis
          dataKey="date"
          stroke="#64748B"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: string) => v.slice(0, 7)}
          interval="preserveStartEnd"
        />

        <YAxis
          stroke="#64748B"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          tickFormatter={yFormatter}
          width={52}
        />

        <Tooltip
          contentStyle={{
            background: "#1A2030",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 8,
            color: "#F1F5F9",
            fontSize: 12,
          }}
          formatter={(value: number | string, name: string) => [tooltipFormatter(value), name]}
          cursor={{ stroke: "rgba(255,255,255,0.10)", strokeWidth: 1 }}
        />

        {series.length > 1 && (
          <Legend
            wrapperStyle={{ fontSize: 12, color: "#94A3B8", paddingTop: 12 }}
            formatter={(value: string) => {
              const s = series.find((x) => x.key === value);
              return s?.label ?? value;
            }}
          />
        )}

        {paddingStart && (
          <ReferenceArea
            x1={paddingStart}
            fill="rgba(148,163,184,0.12)"
            label={{ value: "padding 구간", position: "insideTopRight", fontSize: 10, fill: "#64748B" }}
          />
        )}

        {series.map((s, i) => (
          <Area
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.label}
            stroke={SERIES_COLORS[i % SERIES_COLORS.length]}
            strokeWidth={2}
            fill={`url(#grad-${s.key})`}
            dot={false}
            activeDot={{
              r: 4,
              fill: SERIES_COLORS[i % SERIES_COLORS.length],
              stroke: "#0A0E1A",
              strokeWidth: 2,
            }}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
    </div>
  );
}
