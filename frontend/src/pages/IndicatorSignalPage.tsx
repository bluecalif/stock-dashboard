import { useState, useEffect, useCallback, useRef } from "react";
import { fetchFactors } from "../api/factors";
import { fetchPrices } from "../api/prices";
import { fetchSignals } from "../api/signals";
import {
  fetchSignalAccuracy,
  fetchIndicatorComparison,
} from "../api/analysis";
import type {
  FactorDailyResponse,
  PriceDailyResponse,
  SignalDailyResponse,
  SignalAccuracyResponse,
  IndicatorComparisonResponse,
} from "../types/api";
import FactorChart, {
  mergeMacdData,
  MACDChart,
  getFactorLabel,
} from "../components/charts/FactorChart";
import SignalOverlay from "../components/charts/SignalOverlay";
import IndicatorOverlayChart from "../components/charts/IndicatorOverlayChart";
import AccuracyBarChart from "../components/charts/AccuracyBarChart";
import IndicatorSettingsPanel from "../components/common/IndicatorSettingsPanel";
import type { IndicatorSetting, NormalizeMode } from "../components/common/IndicatorSettingsPanel";
import AssetSelect from "../components/common/AssetSelect";
import { useChartActionStore } from "../store/chartActionStore";
import DateRangePicker from "../components/common/DateRangePicker";
import Loading from "../components/common/Loading";
import ErrorMessage from "../components/common/ErrorMessage";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TABS = [
  { id: "factors", label: "지표 현황" },
  { id: "signals", label: "시그널 타임라인" },
  { id: "accuracy", label: "성공률" },
] as const;

type TabId = (typeof TABS)[number]["id"];

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

const STRATEGIES = [
  { id: "momentum", label: "모멘텀" },
  { id: "trend", label: "추세추종" },
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

function formatValue(factor: string, value: number): string {
  if (factor.startsWith("ret_")) return `${(value * 100).toFixed(2)}%`;
  if (factor === "rsi_14") return value.toFixed(1);
  if (factor === "vol_zscore_20") return value.toFixed(2);
  if (factor === "vol_20") return (value * 100).toFixed(2) + "%";
  return value.toFixed(4);
}

function signalLabel(signal: number): { text: string; color: string } {
  if (signal === 1)
    return { text: "매수", color: "text-green-600 bg-green-50" };
  if (signal === -1)
    return { text: "청산", color: "text-red-600 bg-red-50" };
  return { text: "관망", color: "text-gray-500 bg-gray-50" };
}

function rateColor(rate: number | null): string {
  if (rate == null) return "text-gray-400";
  if (rate >= 0.6) return "text-green-600 font-semibold";
  if (rate <= 0.4) return "text-red-600 font-semibold";
  return "text-gray-700";
}

function fmtPct(v: number | null): string {
  if (v == null) return "—";
  return `${(v * 100).toFixed(1)}%`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function IndicatorSignalPage() {
  const [activeTab, setActiveTab] = useState<TabId>("factors");

  // Shared controls
  const [assetId, setAssetId] = useState("KS200");
  const [startDate, setStartDate] = useState(defaultStart);
  const [endDate, setEndDate] = useState(today);

  // Factors tab
  const [selectedAssetIds, setSelectedAssetIds] = useState<string[]>(["KS200"]);
  const [selectedFactors, setSelectedFactors] = useState<string[]>([
    "rsi_14",
    "macd",
  ]);
  const [factorData, setFactorData] = useState<
    Map<string, FactorDailyResponse[]>
  >(new Map());
  const [latestValues, setLatestValues] = useState<
    Map<string, Map<string, number>>
  >(new Map());
  const [factorPrices, setFactorPrices] = useState<PriceDailyResponse[]>([]);
  const [overlaySettings, setOverlaySettings] = useState<IndicatorSetting[]>(
    [],
  );
  const [normalizeMode, setNormalizeMode] = useState<NormalizeMode>("raw");

  // Signals tab
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([
    "momentum",
  ]);
  const [prices, setPrices] = useState<PriceDailyResponse[]>([]);
  const [signals, setSignals] = useState<SignalDailyResponse[]>([]);
  const [matrixSignals, setMatrixSignals] = useState<SignalDailyResponse[]>([]);

  // Accuracy tab
  const [forwardDays, setForwardDays] = useState(5);
  const [accuracyData, setAccuracyData] = useState<SignalAccuracyResponse[]>(
    [],
  );
  const [comparisonData, setComparisonData] =
    useState<IndicatorComparisonResponse | null>(null);

  // Common
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // Data loaders
  // ---------------------------------------------------------------------------

  const loadFactors = useCallback(async () => {
    if (selectedAssetIds.length === 0 || selectedFactors.length === 0) {
      setFactorData(new Map());
      setLatestValues(new Map());
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const factorsToFetch = new Set<string>(selectedFactors);
      if (factorsToFetch.has("macd")) factorsToFetch.add("ema_12");

      const promises: Promise<{
        factor: string;
        data: FactorDailyResponse[];
      }>[] = [];
      for (const factor of factorsToFetch) {
        for (const aid of selectedAssetIds) {
          promises.push(
            fetchFactors({
              asset_id: aid,
              factor_name: factor,
              start_date: startDate,
              end_date: endDate,
              limit: 500,
            }).then((data) => ({ factor, data })),
          );
        }
      }
      // Fetch prices for overlay chart (in parallel with factors)
      const pricePromises = selectedAssetIds.map((aid) =>
        fetchPrices({
          asset_id: aid,
          start_date: startDate,
          end_date: endDate,
          limit: 500,
        }),
      );

      const [results, ...priceResults] = await Promise.all([
        Promise.all(promises),
        ...pricePromises,
      ]);
      setFactorPrices(priceResults.flat());

      const map = new Map<string, FactorDailyResponse[]>();
      for (const { factor, data } of results) {
        const existing = map.get(factor) || [];
        map.set(factor, [...existing, ...data]);
      }
      setFactorData(map);

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
            if (!latest.has(r.asset_id)) latest.set(r.asset_id, new Map());
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
  }, [selectedAssetIds, selectedFactors, startDate, endDate]);

  const loadSignals = useCallback(async () => {
    if (!assetId || selectedStrategies.length === 0) {
      setPrices([]);
      setSignals([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
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
      setError(err instanceof Error ? err.message : "시그널 데이터 로딩 실패");
    } finally {
      setLoading(false);
    }
  }, [assetId, selectedStrategies, startDate, endDate]);

  const loadMatrix = useCallback(async () => {
    if (!assetId) return;
    try {
      const results = await Promise.all(
        STRATEGIES.map((s) =>
          fetchSignals({ asset_id: assetId, strategy_id: s.id, limit: 1 }),
        ),
      );
      setMatrixSignals(results.flat());
    } catch {
      // silent
    }
  }, [assetId]);

  const loadAccuracy = useCallback(async () => {
    if (!assetId) return;
    setLoading(true);
    setError(null);
    try {
      const [accResults, comparison] = await Promise.all([
        Promise.all(
          STRATEGIES.map((s) =>
            fetchSignalAccuracy({
              asset_id: assetId,
              strategy_id: s.id,
              forward_days: forwardDays,
            }),
          ),
        ),
        fetchIndicatorComparison({
          asset_id: assetId,
          forward_days: forwardDays,
        }),
      ]);
      setAccuracyData(accResults);
      setComparisonData(comparison);
    } catch (err) {
      setError(err instanceof Error ? err.message : "성공률 데이터 로딩 실패");
    } finally {
      setLoading(false);
    }
  }, [assetId, forwardDays]);

  // ---------------------------------------------------------------------------
  // chartActionStore — consume set_filter actions
  // ---------------------------------------------------------------------------

  const filters = useChartActionStore((s) => s.filters);
  const clearFilters = useChartActionStore((s) => s.clearFilters);
  const prevFiltersRef = useRef(filters);

  useEffect(() => {
    if (filters === prevFiltersRef.current) return;
    prevFiltersRef.current = filters;

    // factor_name → 해당 팩터 자동 선택 + 지표 현황 탭 전환
    const factorName = filters.factor_name;
    if (factorName && typeof factorName === "string") {
      setActiveTab("factors");
      setSelectedFactors((prev) =>
        prev.includes(factorName) ? prev : [...prev, factorName],
      );
      clearFilters();
    }

    // strategy_id → 해당 전략 자동 선택 + 시그널 탭 전환
    const strategyId = filters.strategy_id;
    if (strategyId && typeof strategyId === "string") {
      setActiveTab("signals");
      setSelectedStrategies((prev) =>
        prev.includes(strategyId) ? prev : [...prev, strategyId],
      );
      clearFilters();
    }

    // asset_id → 자산 변경
    const assetFilter = filters.asset_id;
    if (assetFilter && typeof assetFilter === "string") {
      setAssetId(assetFilter);
      setSelectedAssetIds((prev) =>
        prev.includes(assetFilter) ? prev : [...prev, assetFilter],
      );
      clearFilters();
    }
  }, [filters, clearFilters]);

  // ---------------------------------------------------------------------------
  // Effects — load data based on active tab
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (activeTab === "factors") loadFactors();
  }, [activeTab, loadFactors]);

  useEffect(() => {
    if (activeTab === "signals") {
      loadSignals();
      loadMatrix();
    }
  }, [activeTab, loadSignals, loadMatrix]);

  useEffect(() => {
    if (activeTab === "accuracy") loadAccuracy();
  }, [activeTab, loadAccuracy]);

  // ---------------------------------------------------------------------------
  // Toggle helpers
  // ---------------------------------------------------------------------------

  const toggleFactor = (f: string) =>
    setSelectedFactors((prev) =>
      prev.includes(f) ? prev.filter((x) => x !== f) : [...prev, f],
    );

  const toggleStrategy = (id: string) =>
    setSelectedStrategies((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id],
    );

  // Overlay visible factors (settings panel 기준, macd 제외)
  const overlayVisibleFactors = selectedFactors
    .filter((f) => f !== "macd")
    .filter((f) => {
      const setting = overlaySettings.find((s) => s.factorName === f);
      return setting ? setting.visible : true; // default visible
    });

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">지표 & 시그널</h2>
        <p className="text-gray-500 mt-1 text-sm">
          기술적 지표 현황 · 매매 시그널 타임라인 · 예측 성공률
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-6">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* ============================================================ */}
      {/* TAB: 지표 현황 */}
      {/* ============================================================ */}
      {activeTab === "factors" && (
        <div className="space-y-6">
          {/* Controls */}
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                자산 선택
              </label>
              <AssetSelect
                value=""
                onChange={() => {}}
                multiple
                selectedIds={selectedAssetIds}
                onChangeMultiple={setSelectedAssetIds}
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

          {/* Charts + Table */}
          {loading ? (
            <Loading message="팩터 데이터 로딩 중..." />
          ) : error ? (
            <ErrorMessage message={error} onRetry={loadFactors} />
          ) : (
            <div className="space-y-6">
              {/* Overlay settings panel */}
              <IndicatorSettingsPanel
                availableFactors={selectedFactors}
                settings={overlaySettings}
                onSettingsChange={setOverlaySettings}
                normalizeMode={normalizeMode}
                onNormalizeModeChange={setNormalizeMode}
              />

              {/* Overlay chart: price + selected indicators */}
              {selectedAssetIds.map((aid) => (
                <div
                  key={`overlay-${aid}`}
                  className="bg-white rounded-lg border border-gray-200 p-4"
                >
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">
                    {aid} — 가격 + 지표 오버레이
                  </h3>
                  <IndicatorOverlayChart
                    prices={factorPrices}
                    factors={factorData}
                    assetId={aid}
                    selectedFactors={overlayVisibleFactors}
                    normalizeMode={normalizeMode}
                  />
                </div>
              ))}

              {/* Individual factor charts */}
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
                      {selectedAssetIds.length === 0 ? (
                        <div className="text-gray-400 text-center py-8">
                          자산을 선택하세요
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {selectedAssetIds.map((aid) => {
                            const macdRecords =
                              factorData.get("macd") || [];
                            const ema12Records =
                              factorData.get("ema_12") || [];
                            const chartData = mergeMacdData(
                              macdRecords,
                              ema12Records,
                              aid,
                            );
                            return (
                              <div key={aid}>
                                <p className="text-xs text-gray-500 mb-1">
                                  {aid}
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
                      assetIds={selectedAssetIds}
                    />
                  )}
                </div>
              ))}

              {/* Factor comparison table */}
              {selectedAssetIds.length > 0 && (
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
                          {selectedAssetIds.map((id) => (
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
                          const hasData = selectedAssetIds.some(
                            (id) =>
                              latestValues.get(id)?.get(factor) !== undefined,
                          );
                          if (!hasData) return null;
                          return (
                            <tr key={factor} className="hover:bg-gray-50">
                              <td className="px-4 py-2 text-gray-700 font-medium">
                                {getFactorLabel(factor)}
                              </td>
                              {selectedAssetIds.map((id) => {
                                const val = latestValues
                                  .get(id)
                                  ?.get(factor);
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
      )}

      {/* ============================================================ */}
      {/* TAB: 시그널 타임라인 */}
      {/* ============================================================ */}
      {activeTab === "signals" && (
        <div className="space-y-6">
          {/* Controls */}
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

          {/* Charts */}
          {loading ? (
            <Loading message="시그널 데이터 로딩 중..." />
          ) : error ? (
            <ErrorMessage message={error} onRetry={loadSignals} />
          ) : (
            <div className="space-y-6">
              {selectedStrategies.map((strategyId) => {
                const stratLabel =
                  STRATEGIES.find((s) => s.id === strategyId)?.label ??
                  strategyId;
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

              {/* Signal matrix */}
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
      )}

      {/* ============================================================ */}
      {/* TAB: 성공률 */}
      {/* ============================================================ */}
      {activeTab === "accuracy" && (
        <div className="space-y-6">
          {/* Controls */}
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                자산 선택
              </label>
              <AssetSelect value={assetId} onChange={setAssetId} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                예측 기간 (거래일)
              </label>
              <div className="flex gap-2">
                {[3, 5, 10, 20].map((d) => (
                  <button
                    key={d}
                    onClick={() => setForwardDays(d)}
                    className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                      forwardDays === d
                        ? "bg-indigo-600 text-white border-indigo-600"
                        : "bg-white text-gray-700 border-gray-300 hover:border-indigo-400"
                    }`}
                  >
                    {d}일
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Content */}
          {loading ? (
            <Loading message="성공률 데이터 로딩 중..." />
          ) : error ? (
            <ErrorMessage message={error} onRetry={loadAccuracy} />
          ) : (
            <div className="space-y-6">
              {/* Strategy accuracy cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {accuracyData.map((acc) => {
                  const stratLabel =
                    STRATEGIES.find((s) => s.id === acc.strategy_id)?.label ??
                    acc.strategy_id;
                  return (
                    <div
                      key={acc.strategy_id}
                      className="bg-white rounded-lg border border-gray-200 p-4"
                    >
                      <h3 className="text-sm font-semibold text-gray-700 mb-3">
                        {stratLabel}
                      </h3>
                      {acc.insufficient_data ? (
                        <p className="text-sm text-gray-400">
                          데이터 불충분 (시그널 {acc.total_signals}개)
                        </p>
                      ) : (
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-500">매수 성공률</span>
                            <span className={rateColor(acc.buy_success_rate)}>
                              {fmtPct(acc.buy_success_rate)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">매도 성공률</span>
                            <span className={rateColor(acc.sell_success_rate)}>
                              {fmtPct(acc.sell_success_rate)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">
                              매수 후 평균수익
                            </span>
                            <span className="text-gray-700">
                              {fmtPct(acc.avg_return_after_buy)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">
                              매도 후 평균수익
                            </span>
                            <span className="text-gray-700">
                              {fmtPct(acc.avg_return_after_sell)}
                            </span>
                          </div>
                          <div className="pt-2 border-t border-gray-100 flex justify-between text-xs text-gray-400">
                            <span>
                              평가 시그널: {acc.evaluated_signals}/
                              {acc.total_signals}
                            </span>
                            <span>{acc.forward_days}일 기준</span>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Accuracy bar chart */}
              {accuracyData.length > 0 && (
                <div className="bg-white rounded-lg border border-gray-200 p-4">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">
                    전략별 성공률 비교 — {assetId} ({forwardDays}일 기준)
                  </h3>
                  <AccuracyBarChart
                    data={accuracyData}
                    strategyLabels={Object.fromEntries(
                      STRATEGIES.map((s) => [s.id, s.label]),
                    )}
                  />
                </div>
              )}

              {/* Comparison ranking table */}
              {comparisonData && (
                <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                  <div className="px-4 py-3 border-b border-gray-200">
                    <h3 className="text-sm font-semibold text-gray-700">
                      예측력 비교 순위 — {assetId} ({forwardDays}일 기준)
                    </h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="px-4 py-2 text-center text-xs font-medium text-gray-500">
                            순위
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                            전략
                          </th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">
                            매수 성공률
                          </th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">
                            매도 성공률
                          </th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">
                            매수 후 수익
                          </th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">
                            매도 후 수익
                          </th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-gray-500">
                            평가 수
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {comparisonData.strategies.map((row) => {
                          const stratLabel =
                            STRATEGIES.find((s) => s.id === row.strategy_id)
                              ?.label ?? row.strategy_id;
                          return (
                            <tr key={row.strategy_id} className="hover:bg-gray-50">
                              <td className="px-4 py-2 text-center font-semibold text-gray-700">
                                {row.rank}
                              </td>
                              <td className="px-4 py-2 font-medium text-gray-700">
                                {stratLabel}
                                {row.insufficient_data && (
                                  <span className="ml-2 text-xs text-gray-400">
                                    (데이터 부족)
                                  </span>
                                )}
                              </td>
                              <td
                                className={`px-4 py-2 text-right tabular-nums ${rateColor(row.buy_success_rate)}`}
                              >
                                {fmtPct(row.buy_success_rate)}
                              </td>
                              <td
                                className={`px-4 py-2 text-right tabular-nums ${rateColor(row.sell_success_rate)}`}
                              >
                                {fmtPct(row.sell_success_rate)}
                              </td>
                              <td className="px-4 py-2 text-right text-gray-600 tabular-nums">
                                {fmtPct(row.avg_return_after_buy)}
                              </td>
                              <td className="px-4 py-2 text-right text-gray-600 tabular-nums">
                                {fmtPct(row.avg_return_after_sell)}
                              </td>
                              <td className="px-4 py-2 text-right text-gray-600 tabular-nums">
                                {row.evaluated_signals}
                              </td>
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
      )}
    </div>
  );
}
