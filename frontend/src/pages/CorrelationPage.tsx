import { useState, useEffect, useCallback } from "react";
import { fetchCorrelation, fetchCorrelationAnalysis, fetchSpread } from "../api/correlation";
import type {
  CorrelationResponse,
  CorrelationAnalysisResponse,
  SpreadResponse,
  AssetPair,
} from "../types/api";
import { useChartActionStore } from "../store/chartActionStore";
import DateRangePicker from "../components/common/DateRangePicker";
import CorrelationHeatmap from "../components/charts/CorrelationHeatmap";
import ScatterPlotChart from "../components/charts/ScatterPlotChart";
import SpreadChart from "../components/charts/SpreadChart";
import CorrelationGroupCard from "../components/correlation/CorrelationGroupCard";
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
  const [analysis, setAnalysis] = useState<CorrelationAnalysisResponse | null>(null);
  const [spread, setSpread] = useState<SpreadResponse | null>(null);
  const [spreadLoading, setSpreadLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const highlightedPair = useChartActionStore((s) => s.highlightedPair);
  const setHighlightedPair = useChartActionStore((s) => s.setHighlightedPair);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [corrResult, analysisResult] = await Promise.all([
        fetchCorrelation({ start_date: startDate, end_date: endDate, window }),
        fetchCorrelationAnalysis({
          start_date: startDate,
          end_date: endDate,
          window,
          top_n: 10,
        }),
      ]);
      setData(corrResult);
      setAnalysis(analysisResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "상관행렬 로딩 실패");
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, window]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Spread 로딩: highlightedPair 변경 시 자동 fetch
  useEffect(() => {
    if (!highlightedPair) {
      setSpread(null);
      return;
    }
    setSpreadLoading(true);
    fetchSpread({
      asset_a: highlightedPair.asset_a,
      asset_b: highlightedPair.asset_b,
      start_date: startDate,
      end_date: endDate,
    })
      .then(setSpread)
      .catch(() => setSpread(null))
      .finally(() => setSpreadLoading(false));
  }, [highlightedPair, startDate, endDate]);

  const handlePairClick = useCallback(
    (pair: AssetPair) => {
      setHighlightedPair({ asset_a: pair.asset_a, asset_b: pair.asset_b });
    },
    [setHighlightedPair],
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">상관도 분석</h2>
        <p className="text-gray-500 mt-1 text-sm">
          자산 간 수익률 상관행렬 · 그룹핑 · 상관 쌍 분포
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

      {loading ? (
        <Loading message="상관행렬 계산 중..." />
      ) : error ? (
        <ErrorMessage message={error} onRetry={loadData} />
      ) : (
        <>
          {/* 그룹핑 카드 */}
          {analysis && analysis.groups.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-3">
                유사 자산 그룹
              </h3>
              <CorrelationGroupCard
                groups={analysis.groups}
                onGroupClick={(g) => {
                  if (g.asset_ids.length >= 2) {
                    setHighlightedPair({
                      asset_a: g.asset_ids[0],
                      asset_b: g.asset_ids[1],
                    });
                  }
                }}
              />
            </div>
          )}

          {/* 히트맵 */}
          {data && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">
                상관행렬 히트맵
              </h3>
              <div className="text-xs text-gray-400 mb-3">
                기간: {data.period.start} ~ {data.period.end} · 윈도우:{" "}
                {data.period.window}일 · 자산 {data.asset_ids.length}개
              </div>
              <CorrelationHeatmap
                assetIds={data.asset_ids}
                matrix={data.matrix}
              />
            </div>
          )}

          {/* Scatter Plot */}
          {analysis && analysis.top_pairs.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">
                상관계수 분포 (Top {analysis.top_pairs.length} 쌍)
              </h3>
              <ScatterPlotChart
                pairs={analysis.top_pairs}
                highlightPair={highlightedPair}
                onPairClick={handlePairClick}
              />
              {highlightedPair && (
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-xs text-amber-600 font-medium">
                    선택: {highlightedPair.asset_a} ↔ {highlightedPair.asset_b}
                  </span>
                  <button
                    onClick={() => setHighlightedPair(null)}
                    className="text-xs text-gray-400 hover:text-gray-600"
                  >
                    해제
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Spread Chart — pair 선택 시 표시 */}
          {highlightedPair && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">
                스프레드 분석 (Z-Score)
              </h3>
              {spreadLoading ? (
                <Loading message="스프레드 계산 중..." />
              ) : spread ? (
                <SpreadChart spread={spread} />
              ) : (
                <p className="text-gray-400 text-sm text-center py-8">
                  스프레드 데이터를 불러올 수 없습니다.
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
