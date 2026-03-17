import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from "recharts";
import type { AnnualPerformanceItem } from "../../types/api";

interface Props {
  data: AnnualPerformanceItem[];
  mode?: "pct" | "amount";
}

function formatPct(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

function formatAmount(v: number): string {
  if (Math.abs(v) >= 1_000_000_000)
    return `${(v / 1_000_000_000).toFixed(1)}억`;
  if (Math.abs(v) >= 10_000)
    return `${(v / 10_000).toFixed(0)}만`;
  return v.toLocaleString("ko-KR");
}

export default function AnnualPerformanceChart({
  data,
  mode = "pct",
}: Props) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-60 text-gray-400 text-sm">
        연간 성과 데이터 없음
      </div>
    );
  }

  const dataKey = mode === "pct" ? "return_pct" : "pnl_amount";
  const formatter = mode === "pct" ? formatPct : formatAmount;

  const chartData = data.map((d) => ({
    ...d,
    label: d.is_partial_year ? `${d.year}*` : `${d.year}`,
  }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 5 }}>
          <XAxis
            dataKey="label"
            tick={{ fontSize: 12 }}
          />
          <YAxis
            tick={{ fontSize: 11 }}
            tickFormatter={formatter}
            width={65}
          />
          <Tooltip
            formatter={(value: number) => [formatter(value), mode === "pct" ? "수익률" : "손익"]}
            labelFormatter={(label: string) => `${label}년`}
            content={({ active, payload, label }) => {
              if (!active || !payload || payload.length === 0) return null;
              const item = payload[0].payload as AnnualPerformanceItem & { label: string };
              return (
                <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-3 text-xs">
                  <div className="font-semibold text-gray-900 mb-1">{label}년</div>
                  <div className="space-y-0.5">
                    <div>
                      수익률:{" "}
                      <span className={item.return_pct >= 0 ? "text-green-600" : "text-red-600"}>
                        {formatPct(item.return_pct)}
                      </span>
                    </div>
                    <div>
                      손익:{" "}
                      <span className={item.pnl_amount >= 0 ? "text-green-600" : "text-red-600"}>
                        ₩{formatAmount(item.pnl_amount)}
                      </span>
                    </div>
                    <div>MDD: {formatPct(item.mdd)}</div>
                    <div>거래: {item.num_trades}회</div>
                    <div>승률: {formatPct(item.win_rate)}</div>
                    {item.is_partial_year && (
                      <div className="text-gray-400 mt-1">
                        * 부분 연도 ({item.trading_days}거래일)
                      </div>
                    )}
                  </div>
                </div>
              );
            }}
          />
          <ReferenceLine y={0} stroke="#d1d5db" />
          <Bar dataKey={dataKey} radius={[4, 4, 0, 0]} maxBarSize={50}>
            {chartData.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.is_favorable ? "#22c55e" : "#ef4444"}
                fillOpacity={entry.is_partial_year ? 0.6 : 1}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* 범례 */}
      <div className="flex items-center justify-center gap-4 mt-2 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-green-500" />
          <span>양호 (수익 + 승률 &gt; 50%)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-red-500" />
          <span>부진</span>
        </div>
        {data.some((d) => d.is_partial_year) && (
          <span className="text-gray-400">* 부분 연도</span>
        )}
      </div>
    </div>
  );
}
