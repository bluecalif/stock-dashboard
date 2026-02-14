import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface EquityPoint {
  date: string;
  [runLabel: string]: number | string;
}

interface Props {
  data: EquityPoint[];
  runLabels: string[];
}

const COLORS = [
  "#2563eb", // blue
  "#dc2626", // red
  "#16a34a", // green
  "#9333ea", // purple
  "#ea580c", // orange
  "#0891b2", // cyan
  "#db2777", // pink
];

function formatEquity(value: number): string {
  if (value >= 1_000_000_000)
    return `${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return value.toFixed(0);
}

export default function EquityCurveChart({ data, runLabels }: Props) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-80 text-gray-400">
        데이터가 없습니다
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data}>
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11 }}
          tickFormatter={(v: string) => v.slice(5)}
        />
        <YAxis
          tick={{ fontSize: 11 }}
          tickFormatter={formatEquity}
          width={70}
        />
        <Tooltip
          labelFormatter={(label: string) => label}
          formatter={(value: number, name: string) => [
            value.toLocaleString(),
            name,
          ]}
        />
        {runLabels.length > 1 && <Legend />}
        {runLabels.map((label, i) => (
          <Line
            key={label}
            type="monotone"
            dataKey={label}
            name={label}
            stroke={COLORS[i % COLORS.length]}
            dot={false}
            strokeWidth={1.5}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

export type { EquityPoint };
