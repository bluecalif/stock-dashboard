import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface PricePoint {
  date: string;
  [assetId: string]: number | string;
}

interface Props {
  data: PricePoint[];
  assetIds: string[];
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

function formatPrice(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return value.toLocaleString();
  return value.toFixed(2);
}

export default function PriceLineChart({ data, assetIds }: Props) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 text-gray-400">
        데이터가 없습니다
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data}>
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12 }}
          tickFormatter={(v: string) => v.slice(5)} // MM-DD
        />
        <YAxis
          tick={{ fontSize: 12 }}
          tickFormatter={formatPrice}
          width={70}
        />
        <Tooltip
          labelFormatter={(label: string) => label}
          formatter={(value: number) => [value.toLocaleString(), ""]}
        />
        {assetIds.length > 1 && <Legend />}
        {assetIds.map((id, i) => (
          <Line
            key={id}
            type="monotone"
            dataKey={id}
            name={id}
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

export type { PricePoint };
