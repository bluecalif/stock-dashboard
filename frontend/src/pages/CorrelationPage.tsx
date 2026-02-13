import { useState, useEffect, useCallback } from "react";
import { fetchCorrelation } from "../api/correlation";
import type { CorrelationResponse } from "../types/api";
import DateRangePicker from "../components/common/DateRangePicker";
import CorrelationHeatmap from "../components/charts/CorrelationHeatmap";
import Loading from "../components/common/Loading";
import ErrorMessage from "../components/common/ErrorMessage";

const WINDOW_OPTIONS = [20, 40, 60, 120, 250];

function defaultStart(): string {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 1);
  return d.toISOString().slice(0, 10);
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function CorrelationPage() {
  const [startDate, setStartDate] = useState(defaultStart);
  const [endDate, setEndDate] = useState(today);
  const [window, setWindow] = useState(60);
  const [data, setData] = useState<CorrelationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCorrelation = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchCorrelation({
        start_date: startDate,
        end_date: endDate,
        window,
      });
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "상관행렬 로딩 실패");
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, window]);

  useEffect(() => {
    loadCorrelation();
  }, [loadCorrelation]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">상관 히트맵</h2>
        <p className="text-gray-500 mt-1 text-sm">
          자산 간 수익률 상관행렬 · 기간/윈도우 조절 가능
        </p>
      </div>

      {/* 필터 영역 */}
      <div className="space-y-3">
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
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            윈도우 (거래일)
          </label>
          <div className="flex gap-2">
            {WINDOW_OPTIONS.map((w) => (
              <button
                key={w}
                onClick={() => setWindow(w)}
                className={`px-3 py-1 rounded text-xs font-medium border transition-colors ${
                  window === w
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
                }`}
              >
                {w}일
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 히트맵 */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        {loading ? (
          <Loading message="상관행렬 계산 중..." />
        ) : error ? (
          <ErrorMessage message={error} onRetry={loadCorrelation} />
        ) : data ? (
          <>
            <div className="text-xs text-gray-400 mb-3">
              기간: {data.period.start} ~ {data.period.end} · 윈도우:{" "}
              {data.period.window}일 · 자산 {data.asset_ids.length}개
            </div>
            <CorrelationHeatmap
              assetIds={data.asset_ids}
              matrix={data.matrix}
            />
          </>
        ) : null}
      </div>
    </div>
  );
}
