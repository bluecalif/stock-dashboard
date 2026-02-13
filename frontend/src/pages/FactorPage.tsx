import { useState, useEffect, useCallback } from "react";
import { fetchFactors } from "../api/factors";
import type { FactorDailyResponse } from "../types/api";
import FactorChart, {
  mergeMacdData,
  MACDChart,
  getFactorLabel,
} from "../components/charts/FactorChart";
import AssetSelect from "../components/common/AssetSelect";
import DateRangePicker from "../components/common/DateRangePicker";
import Loading from "../components/common/Loading";
import ErrorMessage from "../components/common/ErrorMessage";

/** 차트에 표시할 주요 팩터 목록 */
const CHART_FACTORS = [
  "rsi_14",
  "macd",
  "sma_20",
  "sma_60",
  "vol_20",
  "atr_14",
  "ret_1d",
  "ret_5d",
  "roc",
  "vol_zscore_20",
] as const;

/** 비교 테이블에 표시할 팩터 */
const TABLE_FACTORS = [
  "rsi_14",
  "macd",
  "sma_20",
  "sma_60",
  "vol_20",
  "atr_14",
  "ret_1d",
  "ret_5d",
  "ret_20d",
  "ret_63d",
  "roc",
  "vol_zscore_20",
];

function defaultStart(): string {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 1);
  return d.toISOString().slice(0, 10);
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

/** 팩터 유형별 포맷팅 */
function formatValue(factor: string, value: number): string {
  if (factor.startsWith("ret_")) return `${(value * 100).toFixed(2)}%`;
  if (factor === "rsi_14") return value.toFixed(1);
  if (factor === "vol_zscore_20") return value.toFixed(2);
  if (factor === "vol_20") return (value * 100).toFixed(2) + "%";
  return value.toFixed(4);
}

export default function FactorPage() {
  const [selectedIds, setSelectedIds] = useState<string[]>(["KS200"]);
  const [selectedFactors, setSelectedFactors] = useState<string[]>([
    "rsi_14",
    "macd",
  ]);
  const [startDate, setStartDate] = useState(defaultStart);
  const [endDate, setEndDate] = useState(today);
  const [factorData, setFactorData] = useState<
    Map<string, FactorDailyResponse[]>
  >(new Map());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latestValues, setLatestValues] = useState<
    Map<string, Map<string, number>>
  >(new Map());

  const loadFactors = useCallback(async () => {
    if (selectedIds.length === 0 || selectedFactors.length === 0) {
      setFactorData(new Map());
      setLatestValues(new Map());
      return;
    }
    setLoading(true);
    setError(null);
    try {
      // MACD 선택 시 ema_12도 fetch (signal line 용)
      const factorsToFetch = new Set<string>(selectedFactors);
      if (factorsToFetch.has("macd")) {
        factorsToFetch.add("ema_12");
      }

      const promises: Promise<{
        factor: string;
        data: FactorDailyResponse[];
      }>[] = [];

      for (const factor of factorsToFetch) {
        for (const assetId of selectedIds) {
          promises.push(
            fetchFactors({
              asset_id: assetId,
              factor_name: factor,
              start_date: startDate,
              end_date: endDate,
              limit: 500,
            }).then((data) => ({ factor, data })),
          );
        }
      }

      const results = await Promise.all(promises);

      // factorName → FactorDailyResponse[] 병합
      const map = new Map<string, FactorDailyResponse[]>();
      for (const { factor, data } of results) {
        const existing = map.get(factor) || [];
        map.set(factor, [...existing, ...data]);
      }
      setFactorData(map);

      // 최신값 테이블: assetId → factorName → value (가장 최신 날짜)
      const latest = new Map<string, Map<string, number>>();
      for (const [, records] of map) {
        const sorted = [...records].sort((a, b) =>
          b.date.localeCompare(a.date),
        );
        const seen = new Set<string>();
        for (const r of sorted) {
          const key = `${r.asset_id}:${r.factor_name}`;
          if (!seen.has(key)) {
            seen.add(key);
            if (!latest.has(r.asset_id)) {
              latest.set(r.asset_id, new Map());
            }
            latest.get(r.asset_id)!.set(r.factor_name, r.value);
          }
        }
      }
      setLatestValues(latest);
    } catch (err) {
      setError(err instanceof Error ? err.message : "팩터 데이터 로딩 실패");
    } finally {
      setLoading(false);
    }
  }, [selectedIds, selectedFactors, startDate, endDate]);

  useEffect(() => {
    loadFactors();
  }, [loadFactors]);

  const toggleFactor = (factor: string) => {
    setSelectedFactors((prev) =>
      prev.includes(factor)
        ? prev.filter((f) => f !== factor)
        : [...prev, factor],
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">팩터 현황</h2>
        <p className="text-gray-500 mt-1 text-sm">
          RSI · MACD · 이동평균 · 변동성 등 기술적 팩터
        </p>
      </div>

      {/* 필터 영역 */}
      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            자산 선택
          </label>
          <AssetSelect
            value=""
            onChange={() => {}}
            multiple
            selectedIds={selectedIds}
            onChangeMultiple={setSelectedIds}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            팩터 선택
          </label>
          <div className="flex flex-wrap gap-2">
            {CHART_FACTORS.map((f) => {
              const selected = selectedFactors.includes(f);
              return (
                <button
                  key={f}
                  onClick={() => toggleFactor(f)}
                  className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                    selected
                      ? "bg-indigo-600 text-white border-indigo-600"
                      : "bg-white text-gray-700 border-gray-300 hover:border-indigo-400"
                  }`}
                >
                  {getFactorLabel(f)}
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

      {/* 차트 + 테이블 영역 */}
      {loading ? (
        <Loading message="팩터 데이터 로딩 중..." />
      ) : error ? (
        <ErrorMessage message={error} onRetry={loadFactors} />
      ) : (
        <div className="space-y-6">
          {selectedFactors.map((factor) => (
            <div
              key={factor}
              className="bg-white rounded-lg border border-gray-200 p-4"
            >
              {factor === "macd" ? (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">
                    MACD
                  </h3>
                  {selectedIds.length === 0 ? (
                    <div className="text-gray-400 text-center py-8">
                      자산을 선택하세요
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {selectedIds.map((assetId) => {
                        const macdRecords = factorData.get("macd") || [];
                        const ema12Records = factorData.get("ema_12") || [];
                        const chartData = mergeMacdData(
                          macdRecords,
                          ema12Records,
                          assetId,
                        );
                        return (
                          <div key={assetId}>
                            <p className="text-xs text-gray-500 mb-1">
                              {assetId}
                            </p>
                            <MACDChart data={chartData} />
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ) : (
                <FactorChart
                  data={factorData.get(factor) || []}
                  factorName={factor}
                  assetIds={selectedIds}
                />
              )}
            </div>
          ))}

          {/* 팩터 비교 테이블 */}
          {selectedIds.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-200">
                <h3 className="text-sm font-semibold text-gray-700">
                  팩터 비교 (최신값)
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                        팩터
                      </th>
                      {selectedIds.map((id) => (
                        <th
                          key={id}
                          className="px-4 py-2 text-right text-xs font-medium text-gray-500"
                        >
                          {id}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {TABLE_FACTORS.map((factor) => {
                      const hasData = selectedIds.some(
                        (id) =>
                          latestValues.get(id)?.get(factor) !== undefined,
                      );
                      if (!hasData) return null;
                      return (
                        <tr key={factor} className="hover:bg-gray-50">
                          <td className="px-4 py-2 text-gray-700 font-medium">
                            {getFactorLabel(factor)}
                          </td>
                          {selectedIds.map((id) => {
                            const val = latestValues.get(id)?.get(factor);
                            return (
                              <td
                                key={id}
                                className="px-4 py-2 text-right text-gray-600 tabular-nums"
                              >
                                {val !== undefined
                                  ? formatValue(factor, val)
                                  : "—"}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
