import { useState, useEffect, useCallback } from "react";
import { fetchStrategyBacktest } from "../api/analysis";
import type { StrategyBacktestResponse, MetricsItem } from "../types/api";
import AssetSelect from "../components/common/AssetSelect";
import Loading from "../components/common/Loading";
import ErrorMessage from "../components/common/ErrorMessage";
import StrategyDescriptionCard from "../components/strategy/StrategyDescriptionCard";
import type { StrategyName } from "../components/strategy/StrategyDescriptionCard";
import EquityCurveWithEvents from "../components/charts/EquityCurveWithEvents";
import AnnualPerformanceChart from "../components/charts/AnnualPerformanceChart";
import TradeNarrativePanel from "../components/strategy/TradeNarrativePanel";

const PERIODS = ["6M", "1Y", "2Y", "3Y"] as const;
type Period = (typeof PERIODS)[number];

function pct(v: number | null): string {
  return v != null ? `${(v * 100).toFixed(2)}%` : "—";
}

function num2(v: number | null): string {
  return v != null ? v.toFixed(2) : "—";
}

function won(v: number): string {
  return `₩${v.toLocaleString("ko-KR")}`;
}

const METRIC_ROWS: {
  label: string;
  key: keyof MetricsItem;
  fmt: (v: number | null) => string;
}[] = [
  { label: "총수익률", key: "total_return", fmt: pct },
  { label: "CAGR", key: "cagr", fmt: pct },
  { label: "MDD", key: "mdd", fmt: pct },
  { label: "변동성", key: "volatility", fmt: pct },
  { label: "Sharpe", key: "sharpe", fmt: num2 },
  { label: "Sortino", key: "sortino", fmt: num2 },
  { label: "Calmar", key: "calmar", fmt: num2 },
  { label: "승률", key: "win_rate", fmt: pct },
  {
    label: "거래 횟수",
    key: "num_trades",
    fmt: (v) => (v != null ? v.toString() : "—"),
  },
  {
    label: "평균 거래 PnL",
    key: "avg_trade_pnl",
    fmt: (v) => (v != null ? won(v) : "—"),
  },
  { label: "B&H 총수익률", key: "bh_total_return", fmt: pct },
  { label: "B&H CAGR", key: "bh_cagr", fmt: pct },
  { label: "초과수익", key: "excess_return", fmt: pct },
];

export default function StrategyPage() {
  const [assetId, setAssetId] = useState("KS200");
  const [strategy, setStrategy] = useState<StrategyName>("momentum");
  const [period, setPeriod] = useState<Period>("2Y");
  const [annualMode, setAnnualMode] = useState<"pct" | "amount">("pct");

  const [result, setResult] = useState<StrategyBacktestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!assetId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchStrategyBacktest({
        asset_id: assetId,
        strategy_name: strategy,
        period,
        initial_cash: 100_000_000,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "데이터 로딩 실패");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [assetId, strategy, period]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">전략 백테스트</h2>
        <p className="text-gray-500 mt-1 text-sm">
          전략 선택 → 에쿼티 커브, 연간 성과, 거래 내러티브
        </p>
      </div>

      {/* 자산 선택 + 기간 프리셋 */}
      <div className="flex flex-wrap items-end gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            자산 선택
          </label>
          <AssetSelect value={assetId} onChange={setAssetId} />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            기간
          </label>
          <div className="flex gap-1">
            {PERIODS.map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md border transition-colors ${
                  period === p
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
        <div className="text-xs text-gray-400">
          초기 투자금: ₩1억
        </div>
      </div>

      {/* E.6: 전략 설명 카드 */}
      <StrategyDescriptionCard selected={strategy} onSelect={setStrategy} />

      {/* 콘텐츠 */}
      {loading ? (
        <Loading message="백테스트 계산 중..." />
      ) : error ? (
        <ErrorMessage message={error} onRetry={loadData} />
      ) : !result ? (
        <div className="text-center text-gray-400 py-12">
          전략을 선택하면 백테스트 결과가 표시됩니다
        </div>
      ) : (
        <div className="space-y-6">
          {/* 요약 내러티브 */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800 leading-relaxed">
              {result.summary_narrative}
            </p>
          </div>

          {/* E.7: 에쿼티 커브 + 이벤트 마커 */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <EquityCurveWithEvents
              equityCurve={result.equity_curve}
              trades={result.trades}
              strategyLabel={result.strategy_label}
              lossAvoided={result.loss_avoided}
            />
          </div>

          {/* 성과 메트릭스 */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700">
                성과 메트릭스
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <tbody className="divide-y divide-gray-100">
                  {METRIC_ROWS.map((row) => {
                    const val = result.metrics[row.key] as number | null;
                    const isNeg = typeof val === "number" && val < 0;
                    return (
                      <tr key={row.key} className="hover:bg-gray-50">
                        <td className="px-4 py-2 font-medium text-gray-700 w-1/3">
                          {row.label}
                        </td>
                        <td
                          className={`px-4 py-2 text-right tabular-nums ${
                            isNeg ? "text-red-600" : "text-gray-700"
                          }`}
                        >
                          {row.fmt(val)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* E.8: 연간 성과 차트 */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-gray-700">
                연간 성과
              </h3>
              <div className="flex gap-1">
                <button
                  onClick={() => setAnnualMode("pct")}
                  className={`px-2 py-1 text-xs rounded ${
                    annualMode === "pct"
                      ? "bg-gray-200 text-gray-800 font-medium"
                      : "text-gray-500 hover:bg-gray-100"
                  }`}
                >
                  수익률 %
                </button>
                <button
                  onClick={() => setAnnualMode("amount")}
                  className={`px-2 py-1 text-xs rounded ${
                    annualMode === "amount"
                      ? "bg-gray-200 text-gray-800 font-medium"
                      : "text-gray-500 hover:bg-gray-100"
                  }`}
                >
                  금액 ₩
                </button>
              </div>
            </div>
            <AnnualPerformanceChart
              data={result.annual_performance}
              mode={annualMode}
            />
          </div>

          {/* E.7: 거래 내러티브 패널 */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <TradeNarrativePanel
              trades={result.trades}
              strategyLabel={result.strategy_label}
            />
          </div>
        </div>
      )}
    </div>
  );
}
