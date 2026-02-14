import { useState, useEffect, useCallback } from "react";
import { fetchPrices } from "../api/prices";
import { fetchSignals } from "../api/signals";
import type {
  PriceDailyResponse,
  SignalDailyResponse,
} from "../types/api";
import SignalOverlay from "../components/charts/SignalOverlay";
import AssetSelect from "../components/common/AssetSelect";
import DateRangePicker from "../components/common/DateRangePicker";
import Loading from "../components/common/Loading";
import ErrorMessage from "../components/common/ErrorMessage";

const STRATEGIES = [
  { id: "momentum", label: "모멘텀" },
  { id: "trend_follow", label: "추세추종" },
  { id: "mean_reversion", label: "평균회귀" },
] as const;

function defaultStart(): string {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 1);
  return d.toISOString().slice(0, 10);
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

/** 시그널 값 → 텍스트 */
function signalLabel(signal: number): { text: string; color: string } {
  if (signal === 1) return { text: "매수", color: "text-green-600 bg-green-50" };
  if (signal === -1) return { text: "청산", color: "text-red-600 bg-red-50" };
  return { text: "관망", color: "text-gray-500 bg-gray-50" };
}

export default function SignalPage() {
  const [assetId, setAssetId] = useState("KS200");
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([
    "momentum",
  ]);
  const [startDate, setStartDate] = useState(defaultStart);
  const [endDate, setEndDate] = useState(today);

  const [prices, setPrices] = useState<PriceDailyResponse[]>([]);
  const [signals, setSignals] = useState<SignalDailyResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 매트릭스용: 전략별 최신 시그널 (모든 전략)
  const [matrixSignals, setMatrixSignals] = useState<SignalDailyResponse[]>([]);

  const loadData = useCallback(async () => {
    if (!assetId || selectedStrategies.length === 0) {
      setPrices([]);
      setSignals([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      // 가격 + 선택 전략 시그널 병렬 fetch
      const [priceData, ...signalResults] = await Promise.all([
        fetchPrices({
          asset_id: assetId,
          start_date: startDate,
          end_date: endDate,
          limit: 500,
        }),
        ...selectedStrategies.map((strategyId) =>
          fetchSignals({
            asset_id: assetId,
            strategy_id: strategyId,
            start_date: startDate,
            end_date: endDate,
            limit: 500,
          }),
        ),
      ]);
      setPrices(priceData);
      setSignals(signalResults.flat());
    } catch (err) {
      setError(err instanceof Error ? err.message : "데이터 로딩 실패");
    } finally {
      setLoading(false);
    }
  }, [assetId, selectedStrategies, startDate, endDate]);

  // 매트릭스: 모든 전략의 최신 시그널 (assetId 변경 시)
  const loadMatrix = useCallback(async () => {
    if (!assetId) return;
    try {
      const results = await Promise.all(
        STRATEGIES.map((s) =>
          fetchSignals({
            asset_id: assetId,
            strategy_id: s.id,
            limit: 1,
          }),
        ),
      );
      setMatrixSignals(results.flat());
    } catch {
      // 매트릭스 실패해도 메인 차트는 유지
    }
  }, [assetId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    loadMatrix();
  }, [loadMatrix]);

  const toggleStrategy = (id: string) => {
    setSelectedStrategies((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id],
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">시그널 타임라인</h2>
        <p className="text-gray-500 mt-1 text-sm">
          가격 차트 위에 매매 시그널 마커 오버레이
        </p>
      </div>

      {/* 필터 영역 */}
      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            자산 선택
          </label>
          <AssetSelect value={assetId} onChange={setAssetId} />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            전략 선택
          </label>
          <div className="flex flex-wrap gap-2">
            {STRATEGIES.map((s) => {
              const selected = selectedStrategies.includes(s.id);
              return (
                <button
                  key={s.id}
                  onClick={() => toggleStrategy(s.id)}
                  className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                    selected
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
                  }`}
                >
                  {s.label}
                </button>
              );
            })}
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            기간
          </label>
          <DateRangePicker
            startDate={startDate}
            endDate={endDate}
            onStartChange={setStartDate}
            onEndChange={setEndDate}
          />
        </div>
      </div>

      {/* 차트 영역 */}
      {loading ? (
        <Loading message="시그널 데이터 로딩 중..." />
      ) : error ? (
        <ErrorMessage message={error} onRetry={loadData} />
      ) : (
        <div className="space-y-6">
          {selectedStrategies.map((strategyId) => {
            const stratLabel =
              STRATEGIES.find((s) => s.id === strategyId)?.label ?? strategyId;
            return (
              <div
                key={strategyId}
                className="bg-white rounded-lg border border-gray-200 p-4"
              >
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  {assetId} — {stratLabel}
                </h3>
                <SignalOverlay
                  prices={prices}
                  signals={signals}
                  assetId={assetId}
                  strategyId={strategyId}
                />
              </div>
            );
          })}

          {/* 시그널 매트릭스 */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700">
                전략 시그널 매트릭스 — {assetId}
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                      전략
                    </th>
                    <th className="px-4 py-2 text-center text-xs font-medium text-gray-500">
                      최신 시그널
                    </th>
                    <th className="px-4 py-2 text-center text-xs font-medium text-gray-500">
                      날짜
                    </th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">
                      스코어
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                      액션
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {STRATEGIES.map((s) => {
                    const latest = matrixSignals.find(
                      (sig) => sig.strategy_id === s.id,
                    );
                    const sl = latest
                      ? signalLabel(latest.signal)
                      : { text: "—", color: "text-gray-400" };
                    return (
                      <tr key={s.id} className="hover:bg-gray-50">
                        <td className="px-4 py-2 font-medium text-gray-700">
                          {s.label}
                        </td>
                        <td className="px-4 py-2 text-center">
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${sl.color}`}
                          >
                            {sl.text}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-center text-gray-600 tabular-nums">
                          {latest?.date ?? "—"}
                        </td>
                        <td className="px-4 py-2 text-right text-gray-600 tabular-nums">
                          {latest?.score != null
                            ? latest.score.toFixed(2)
                            : "—"}
                        </td>
                        <td className="px-4 py-2 text-gray-600">
                          {latest?.action ?? "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
