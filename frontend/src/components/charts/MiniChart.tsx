import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";

interface DataPoint {
  date: string;
  close: number;
}

interface Props {
  data: DataPoint[];
  color?: string;
  width?: number;
  height?: number;
}

export default function MiniChart({
  data,
  color = "#2563eb",
  width = 120,
  height = 40,
}: Props) {
  if (data.length === 0) return null;

  const isUp = data[data.length - 1].close >= data[0].close;
  const lineColor = color === "#2563eb" ? (isUp ? "#16a34a" : "#dc2626") : color;

  return (
    <div style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <YAxis domain={["dataMin", "dataMax"]} hide />
          <Line
            type="monotone"
            dataKey="close"
            stroke={lineColor}
            dot={false}
            strokeWidth={1.5}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
