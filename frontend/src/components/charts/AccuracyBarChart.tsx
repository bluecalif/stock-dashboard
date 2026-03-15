import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
  Cell,
} from "recharts";
import type { SignalAccuracyResponse } from "../../types/api";

interface Props {
  data: SignalAccuracyResponse[];
  strategyLabels: Record<string, string>;
}

interface ChartRow {
  strategy: string;
  buy: number;
  sell: number;
}

function barColor(rate: number): string {
  if (rate >= 60) return "#16a34a"; // green
  if (rate <= 40) return "#dc2626"; // red
  return "#6b7280"; // gray
}

export default function AccuracyBarChart({ data, strategyLabels }: Props) {
  const chartData: ChartRow[] = data
    .filter((d) => !d.insufficient_data)
    .map((d) => ({
      strategy: strategyLabels[d.strategy_id] ?? d.strategy_id,
      buy: d.buy_success_rate != null ? d.buy_success_rate * 100 : 0,
      sell: d.sell_success_rate != null ? d.sell_success_rate * 100 : 0,
    }));

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        성공률 데이터가 없습니다
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} barGap={4} barCategoryGap="25%">
        <XAxis dataKey="strategy" tick={{ fontSize: 12 }} />
        <YAxis
          tick={{ fontSize: 11 }}
          domain={[0, 100]}
          ticks={[0, 20, 40, 60, 80, 100]}
          tickFormatter={(v: number) => `${v}%`}
          width={45}
        />
        <Tooltip
          formatter={(value: number, name: string) => [
            `${value.toFixed(1)}%`,
            name === "buy" ? "매수 성공률" : "매도 성공률",
          ]}
        />
        <Legend
          formatter={(value: string) =>
            value === "buy" ? "매수 성공률" : "매도 성공률"
          }
        />
        <ReferenceLine
          y={50}
          stroke="#9ca3af"
          strokeDasharray="4 4"
          label={{ value: "50%", position: "right", fontSize: 10, fill: "#9ca3af" }}
        />
        <Bar dataKey="buy" name="buy" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={`buy-${i}`} fill={barColor(entry.buy)} />
          ))}
        </Bar>
        <Bar dataKey="sell" name="sell" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={`sell-${i}`} fill={barColor(entry.sell)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
