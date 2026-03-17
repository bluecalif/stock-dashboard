import { useState, useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceDot,
  ReferenceArea,
} from "recharts";
import type {
  EquityCurveItem,
  TradeItem,
} from "../../types/api";

interface Props {
  equityCurve: EquityCurveItem[];
  trades: TradeItem[];
  strategyLabel: string;
  lossAvoided: number | null;
  showBuyAndHold?: boolean;
}

interface ChartPoint {
  date: string;
  equity: number;
  bh_equity: number | null;
  drawdown: number;
}

function formatEquity(value: number): string {
  if (value >= 1_000_000_000)
    return `${(value / 1_000_000_000).toFixed(1)}B`;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(0)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return value.toFixed(0);
}

function formatWon(v: number): string {
  if (Math.abs(v) >= 1_000_000_000)
    return `${(v / 1_000_000_000).toFixed(1)}억`;
  if (Math.abs(v) >= 10_000)
    return `${(v / 10_000).toFixed(0)}만`;
  return v.toLocaleString("ko-KR");
}

export default function EquityCurveWithEvents({
  equityCurve,
  trades,
  strategyLabel,
  lossAvoided,
  showBuyAndHold = true,
}: Props) {
  const [selectedTrade, setSelectedTrade] = useState<TradeItem | null>(null);

  const data: ChartPoint[] = useMemo(
    () =>
      equityCurve.map((p) => ({
        date: p.date,
        equity: p.equity,
        bh_equity: p.bh_equity,
        drawdown: p.drawdown,
      })),
    [equityCurve],
  );

  // Best/Worst 구간 계산
  const bestTrade = useMemo(
    () => trades.find((t) => t.is_best && t.pnl != null),
    [trades],
  );
  const worstTrade = useMemo(
    () => trades.find((t) => t.is_worst && t.pnl != null),
    [trades],
  );

  // 매수/매도 마커 데이터
  const markers = useMemo(() => {
    const result: {
      date: string;
      equity: number;
      type: "buy" | "sell";
      trade: TradeItem;
    }[] = [];
    const equityMap = new Map(data.map((p) => [p.date, p.equity]));

    for (const trade of trades) {
      const entryEquity = equityMap.get(trade.entry_date);
      if (entryEquity != null) {
        result.push({
          date: trade.entry_date,
          equity: entryEquity,
          type: "buy",
          trade,
        });
      }
      if (trade.exit_date) {
        const exitEquity = equityMap.get(trade.exit_date);
        if (exitEquity != null) {
          result.push({
            date: trade.exit_date,
            equity: exitEquity,
            type: "sell",
            trade,
          });
        }
      }
    }
    return result;
  }, [trades, data]);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-80 text-gray-400">
        데이터가 없습니다
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-700">
          에쿼티 커브 — {strategyLabel}
        </h3>
        {lossAvoided != null && lossAvoided > 0 && (
          <span className="text-xs bg-amber-50 text-amber-700 px-2 py-1 rounded-full font-medium">
            회피 손실: ₩{formatWon(lossAvoided)}
          </span>
        )}
      </div>

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
              `₩${value.toLocaleString("ko-KR")}`,
              name,
            ]}
          />
          <Legend />

          {/* Best 구간 (초록 하이라이트) */}
          {bestTrade && bestTrade.exit_date && (
            <ReferenceArea
              x1={bestTrade.entry_date}
              x2={bestTrade.exit_date}
              fill="#22c55e"
              fillOpacity={0.08}
              stroke="#22c55e"
              strokeOpacity={0.3}
              label={{
                value: `+₩${formatWon(bestTrade.pnl!)}`,
                position: "insideTopRight",
                fontSize: 11,
                fill: "#16a34a",
                fontWeight: 600,
              }}
            />
          )}

          {/* Worst 구간 (빨강 하이라이트) */}
          {worstTrade && worstTrade.exit_date && (
            <ReferenceArea
              x1={worstTrade.entry_date}
              x2={worstTrade.exit_date}
              fill="#ef4444"
              fillOpacity={0.08}
              stroke="#ef4444"
              strokeOpacity={0.3}
              label={{
                value: `₩${formatWon(worstTrade.pnl!)}`,
                position: "insideTopRight",
                fontSize: 11,
                fill: "#dc2626",
                fontWeight: 600,
              }}
            />
          )}

          {/* 전략 에쿼티 */}
          <Line
            type="monotone"
            dataKey="equity"
            name={strategyLabel}
            stroke="#2563eb"
            dot={false}
            strokeWidth={2}
            connectNulls
          />

          {/* B&H 에쿼티 */}
          {showBuyAndHold && (
            <Line
              type="monotone"
              dataKey="bh_equity"
              name="Buy & Hold"
              stroke="#9ca3af"
              dot={false}
              strokeWidth={1}
              strokeDasharray="4 2"
              connectNulls
            />
          )}

          {/* 매수 마커 (초록) */}
          {markers
            .filter((m) => m.type === "buy")
            .map((m) => (
              <ReferenceDot
                key={`buy-${m.date}`}
                x={m.date}
                y={m.equity}
                r={4}
                fill="#22c55e"
                stroke="#fff"
                strokeWidth={1}
                onClick={() => setSelectedTrade(m.trade)}
                style={{ cursor: "pointer" }}
              />
            ))}

          {/* 매도 마커 (빨강) */}
          {markers
            .filter((m) => m.type === "sell")
            .map((m) => (
              <ReferenceDot
                key={`sell-${m.date}`}
                x={m.date}
                y={m.equity}
                r={4}
                fill="#ef4444"
                stroke="#fff"
                strokeWidth={1}
                onClick={() => setSelectedTrade(m.trade)}
                style={{ cursor: "pointer" }}
              />
            ))}
        </LineChart>
      </ResponsiveContainer>

      {/* 선택된 거래 내러티브 */}
      {selectedTrade && (
        <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200 relative">
          <button
            onClick={() => setSelectedTrade(null)}
            className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 text-sm"
          >
            ✕
          </button>
          <div className="flex items-center gap-2 mb-2">
            {selectedTrade.is_best && (
              <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium">
                최고 수익
              </span>
            )}
            {selectedTrade.is_worst && (
              <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">
                최대 손실
              </span>
            )}
            <span className="text-xs text-gray-500">
              {selectedTrade.entry_date} → {selectedTrade.exit_date ?? "보유 중"}{" "}
              ({selectedTrade.holding_days}일)
            </span>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed">
            {selectedTrade.narrative}
          </p>
          {selectedTrade.pnl != null && (
            <div className="mt-2 flex gap-4 text-xs">
              <span
                className={
                  selectedTrade.pnl >= 0 ? "text-green-600" : "text-red-600"
                }
              >
                손익: ₩{selectedTrade.pnl.toLocaleString("ko-KR")}
              </span>
              {selectedTrade.pnl_pct != null && (
                <span
                  className={
                    selectedTrade.pnl_pct >= 0
                      ? "text-green-600"
                      : "text-red-600"
                  }
                >
                  수익률: {(selectedTrade.pnl_pct * 100).toFixed(2)}%
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
