import {
  ComposedChart,
  Line,
  Bar,
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

function formatVolume(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return value.toString();
}

export default function PriceLineChart({ data, assetIds }: Props) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 text-gray-400">
        데이터가 없습니다
      </div>
    );
  }

  // 단일 자산일 때만 거래량 표시
  const showVolume = assetIds.length === 1;
  const volKey = showVolume ? `${assetIds[0]}_vol` : "";
  const hasVolume =
    showVolume && data.some((d) => typeof d[volKey] === "number" && d[volKey] > 0);

  return (
    <div>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={data}>
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(v: string) => v.slice(5)}
          />
          <YAxis
            yAxisId="price"
            tick={{ fontSize: 12 }}
            tickFormatter={formatPrice}
            width={70}
          />
          {hasVolume && (
            <YAxis
              yAxisId="volume"
              orientation="right"
              tick={{ fontSize: 10 }}
              tickFormatter={formatVolume}
              width={50}
            />
          )}
          <Tooltip
            labelFormatter={(label: string) => label}
            formatter={(value: number, name: string) => {
              if (name.endsWith("_vol"))
                return [value.toLocaleString(), "거래량"];
              return [value.toLocaleString(), name];
            }}
          />
          {assetIds.length > 1 && <Legend />}
          {hasVolume && (
            <Bar
              yAxisId="volume"
              dataKey={volKey}
              name={`${assetIds[0]}_vol`}
              fill="#e5e7eb"
              opacity={0.5}
              legendType="none"
            />
          )}
          {assetIds.map((id, i) => (
            <Line
              key={id}
              yAxisId="price"
              type="monotone"
              dataKey={id}
              name={id}
              stroke={COLORS[i % COLORS.length]}
              dot={false}
              strokeWidth={1.5}
              connectNulls
            />
          ))}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export type { PricePoint };
