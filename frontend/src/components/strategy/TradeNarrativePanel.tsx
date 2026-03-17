import type { TradeItem } from "../../types/api";

interface Props {
  trades: TradeItem[];
  strategyLabel: string;
}

export default function TradeNarrativePanel({ trades, strategyLabel }: Props) {
  if (trades.length === 0) {
    return (
      <div className="text-center text-gray-400 py-6 text-sm">
        거래 내역 없음
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-700">
        거래 내러티브 — {strategyLabel}
      </h3>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {trades.map((trade, i) => {
          const isProfit = trade.pnl != null && trade.pnl > 0;
          const isLoss = trade.pnl != null && trade.pnl < 0;

          return (
            <div
              key={`${trade.entry_date}-${i}`}
              className={`p-3 rounded-lg border ${
                trade.is_best
                  ? "border-green-200 bg-green-50/50"
                  : trade.is_worst
                    ? "border-red-200 bg-red-50/50"
                    : "border-gray-200 bg-white"
              }`}
            >
              {/* 헤더 */}
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 tabular-nums">
                    #{i + 1}
                  </span>
                  {trade.is_best && (
                    <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-medium">
                      최고 수익
                    </span>
                  )}
                  {trade.is_worst && (
                    <span className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-medium">
                      최대 손실
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 text-xs tabular-nums">
                  {trade.pnl != null && (
                    <span
                      className={
                        isProfit
                          ? "text-green-600 font-medium"
                          : isLoss
                            ? "text-red-600 font-medium"
                            : "text-gray-500"
                      }
                    >
                      ₩{trade.pnl.toLocaleString("ko-KR")}
                    </span>
                  )}
                  {trade.pnl_pct != null && (
                    <span
                      className={
                        isProfit
                          ? "text-green-600"
                          : isLoss
                            ? "text-red-600"
                            : "text-gray-500"
                      }
                    >
                      {(trade.pnl_pct * 100).toFixed(2)}%
                    </span>
                  )}
                </div>
              </div>

              {/* 기간 */}
              <div className="text-xs text-gray-500 mb-2">
                {trade.entry_date} → {trade.exit_date ?? "보유 중"}{" "}
                <span className="text-gray-400">
                  ({trade.holding_days}일)
                </span>
              </div>

              {/* 내러티브 */}
              <p className="text-sm text-gray-700 leading-relaxed">
                {trade.narrative}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
