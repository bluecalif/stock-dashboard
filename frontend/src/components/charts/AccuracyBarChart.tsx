import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
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

const BUY_COLOR = "#16a34a";  // green — always for buy
const SELL_COLOR = "#dc2626"; // red — always for sell

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
        <Bar dataKey="buy" name="buy" fill={BUY_COLOR} radius={[4, 4, 0, 0]} />
        <Bar dataKey="sell" name="sell" fill={SELL_COLOR} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
