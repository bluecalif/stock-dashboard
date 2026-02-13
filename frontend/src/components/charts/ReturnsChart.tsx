import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from "recharts";

/** date + 각 assetId별 정규화 수익률(기준일=100) */
interface ReturnsPoint {
  date: string;
  [assetId: string]: number | string;
}

interface Props {
  data: ReturnsPoint[];
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

export default function ReturnsChart({ data, assetIds }: Props) {
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
          tickFormatter={(v: string) => v.slice(5)}
        />
        <YAxis
          tick={{ fontSize: 12 }}
          tickFormatter={(v: number) => v.toFixed(0)}
          width={50}
          domain={["auto", "auto"]}
        />
        <Tooltip
          labelFormatter={(label: string) => label}
          formatter={(value: number, name: string) => [
            `${value.toFixed(2)}`,
            name,
          ]}
        />
        <ReferenceLine y={100} stroke="#9ca3af" strokeDasharray="4 4" />
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

export type { ReturnsPoint };
