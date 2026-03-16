import { useState, useEffect, useCallback, useRef } from "react";
import { fetchPrices } from "../api/prices";
import { fetchFactors } from "../api/factors";
import {
  fetchIndicatorSignals,
  fetchIndicatorAccuracy,
  fetchIndicatorComparisonV2,
} from "../api/analysis";
import type {
  PriceDailyResponse,
  FactorDailyResponse,
  SignalAccuracyResponse,
  IndicatorSignalItem,
  IndicatorComparisonResponseV2,
} from "../types/api";
import IndicatorOverlayChart from "../components/charts/IndicatorOverlayChart";
import AccuracyBarChart from "../components/charts/AccuracyBarChart";
import AssetSelect from "../components/common/AssetSelect";
import { useChartActionStore } from "../store/chartActionStore";
import DateRangePicker from "../components/common/DateRangePicker";
import Loading from "../components/common/Loading";
import ErrorMessage from "../components/common/ErrorMessage";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TABS = [
  { id: "signals", label: "시그널" },
  { id: "accuracy", label: "성공률" },
] as const;

type TabId = (typeof TABS)[number]["id"];

const INDICATORS = [
  { id: "rsi_14", label: "RSI" },
  { id: "macd", label: "MACD" },
  { id: "atr_vol", label: "ATR+변동성" },
] as const;

const INDICATOR_FACTOR_MAP: Record<string, string[]> = {
  rsi_14: ["rsi_14"],
  macd: ["macd", "macd_signal"],
  atr_vol: ["atr_14", "vol_20"],
};

const INDICATOR_LABELS: Record<string, string> = Object.fromEntries(
  INDICATORS.map((i) => [i.id, i.label]),
);

const INDICATOR_DESCRIPTIONS: Record<string, string> = {
  rsi_14: "RSI 14일 — 30 이하 진입 시 매수, 70 이상 진입 시 매도, 복귀 시 해제",
  macd: "MACD 히스토그램 — 양(+)전환 시 매수(골든크로스), 음(-)전환 시 매도(데드크로스)",
  atr_vol: "ATR/가격 > 3% 또는 변동성 > 30% 시 고변동성 경고",
};

function defaultStart(): string {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 1);
  return d.toISOString().slice(0, 10);
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
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

function signalBadge(signal: number): { text: string; className: string } {
  if (signal === 1)
    return { text: "매수", className: "text-green-600 bg-green-50" };
  if (signal === -1)
    return { text: "매도", className: "text-red-600 bg-red-50" };
  if (signal === 2)
    return { text: "매수해제", className: "text-blue-600 bg-blue-50" };
  if (signal === -2)
    return { text: "매도해제", className: "text-orange-600 bg-orange-50" };
  return { text: "경고", className: "text-amber-600 bg-amber-50" };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function IndicatorSignalPage() {
  const [activeTab, setActiveTab] = useState<TabId>("signals");

  // Shared controls
  const [assetId, setAssetId] = useState("KS200");
  const [startDate, setStartDate] = useState(defaultStart);
  const [endDate, setEndDate] = useState(today);
  const [selectedIndicator, setSelectedIndicator] = useState("rsi_14");

  // Signals tab
  const [prices, setPrices] = useState<PriceDailyResponse[]>([]);
  const [indicatorSignals, setIndicatorSignals] = useState<
    IndicatorSignalItem[]
  >([]);
  const [factorData, setFactorData] = useState<
    Map<string, FactorDailyResponse[]>
  >(new Map());

  // Accuracy tab
  const [forwardDays, setForwardDays] = useState(5);
  const [accuracyData, setAccuracyData] = useState<SignalAccuracyResponse[]>(
    [],
  );
  const [comparisonData, setComparisonData] =
    useState<IndicatorComparisonResponseV2 | null>(null);

  // Common
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // Data loaders
  // ---------------------------------------------------------------------------

  const loadSignals = useCallback(async () => {
    if (!assetId) return;
    setLoading(true);
    setError(null);
    try {
      const factorNames = INDICATOR_FACTOR_MAP[selectedIndicator] ?? [];
      const [priceData, signalData, ...factorResults] = await Promise.all([
        fetchPrices({
          asset_id: assetId,
          start_date: startDate,
          end_date: endDate,
          limit: 500,
        }),
        fetchIndicatorSignals({
          asset_id: assetId,
          indicator_id: selectedIndicator,
          start_date: startDate,
          end_date: endDate,
        }),
        ...factorNames.map((name) =>
          fetchFactors({
            asset_id: assetId,
            factor_name: name,
            start_date: startDate,
            end_date: endDate,
            limit: 500,
          }),
        ),
      ]);
      setPrices(priceData);
      setIndicatorSignals(signalData.signals);
      const newFactorMap = new Map<string, FactorDailyResponse[]>();
      factorNames.forEach((name, i) => {
        newFactorMap.set(name, factorResults[i]);
      });
      setFactorData(newFactorMap);
    } catch (err) {
      setError(err instanceof Error ? err.message : "시그널 데이터 로딩 실패");
    } finally {
      setLoading(false);
    }
  }, [assetId, selectedIndicator, startDate, endDate]);

  const loadAccuracy = useCallback(async () => {
    if (!assetId) return;
    setLoading(true);
    setError(null);
    try {
      const [acc, comparison] = await Promise.all([
        fetchIndicatorAccuracy({
          asset_id: assetId,
          indicator_id: selectedIndicator,
          forward_days: forwardDays,
          include_details: true,
          start_date: startDate,
          end_date: endDate,
        }),
        fetchIndicatorComparisonV2({
          asset_id: assetId,
          forward_days: forwardDays,
          start_date: startDate,
          end_date: endDate,
        }),
      ]);
      setAccuracyData([acc]);
      setComparisonData(comparison);
    } catch (err) {
      setError(err instanceof Error ? err.message : "성공률 데이터 로딩 실패");
    } finally {
      setLoading(false);
    }
  }, [assetId, selectedIndicator, forwardDays, startDate, endDate]);

  // ---------------------------------------------------------------------------
  // chartActionStore — consume set_filter actions
  // ---------------------------------------------------------------------------

  const filters = useChartActionStore((s) => s.filters);
  const clearFilters = useChartActionStore((s) => s.clearFilters);
  const prevFiltersRef = useRef(filters);

  useEffect(() => {
    if (filters === prevFiltersRef.current) return;
    prevFiltersRef.current = filters;

    const indicatorId = filters.indicator_id ?? filters.factor_name;
    if (indicatorId && typeof indicatorId === "string") {
      const matched = INDICATORS.find((i) => i.id === indicatorId);
      if (matched) {
        setActiveTab("signals");
        setSelectedIndicator(matched.id);
      }
      clearFilters();
    }

    const assetFilter = filters.asset_id;
    if (assetFilter && typeof assetFilter === "string") {
      setAssetId(assetFilter);
      clearFilters();
    }
  }, [filters, clearFilters]);

  // ---------------------------------------------------------------------------
  // Effects
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (activeTab === "signals") loadSignals();
  }, [activeTab, loadSignals]);

  useEffect(() => {
    if (activeTab === "accuracy") loadAccuracy();
  }, [activeTab, loadAccuracy]);

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">지표 & 시그널</h2>
        <p className="text-gray-500 mt-1 text-sm">
          RSI · MACD · ATR+변동성 시그널 분석 및 성공률
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
      {/* TAB: 시그널 */}
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
                지표 선택
              </label>
              <div className="flex flex-wrap gap-2">
                {INDICATORS.map((ind) => (
                  <button
                    key={ind.id}
                    onClick={() => setSelectedIndicator(ind.id)}
                    className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                      selectedIndicator === ind.id
                        ? "bg-indigo-600 text-white border-indigo-600"
                        : "bg-white text-gray-700 border-gray-300 hover:border-indigo-400"
                    }`}
                  >
                    {ind.label}
                  </button>
                ))}
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

          {/* Content: 3/4 chart + 1/4 description */}
          {loading ? (
            <Loading message="시그널 데이터 로딩 중..." />
          ) : error ? (
            <ErrorMessage message={error} onRetry={loadSignals} />
          ) : (
            <div className="grid grid-cols-4 gap-4">
              {/* Chart 3/4 */}
              <div className="col-span-3 bg-white rounded-lg border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">
                  {assetId} — {INDICATOR_LABELS[selectedIndicator] ?? selectedIndicator} 시그널
                </h3>
                <IndicatorOverlayChart
                  prices={prices}
                  factors={factorData}
                  assetId={assetId}
                  selectedFactors={INDICATOR_FACTOR_MAP[selectedIndicator] ?? []}
                  signalDates={indicatorSignals}
                  indicatorId={selectedIndicator}
                />
              </div>

              {/* Description panel 1/4 */}
              <div className="col-span-1 bg-white rounded-lg border border-gray-200 p-4 space-y-4">
                {/* 지표 설명 카드 (DI.1) */}
                <div className="bg-indigo-50 border border-indigo-100 rounded p-2">
                  <p className="text-xs text-indigo-700 leading-relaxed">
                    {INDICATOR_DESCRIPTIONS[selectedIndicator]}
                  </p>
                </div>
                <h3 className="text-sm font-semibold text-gray-700">
                  시그널 이력
                </h3>
                <p className="text-xs text-gray-400">
                  총 {indicatorSignals.length}건
                </p>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {indicatorSignals.length === 0 ? (
                    <p className="text-sm text-gray-400">
                      해당 기간에 시그널이 없습니다
                    </p>
                  ) : (
                    indicatorSignals.map((sig, i) => {
                      const badge = signalBadge(sig.signal);
                      return (
                        <div
                          key={i}
                          className="border border-gray-100 rounded p-2 text-xs"
                        >
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-gray-500 tabular-nums">
                              {sig.date}
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded text-xs font-medium ${badge.className}`}
                            >
                              {badge.text}
                            </span>
                          </div>
                          <p className="text-gray-700">{sig.label}</p>
                          <p className="text-gray-400 tabular-nums">
                            가격: {sig.entry_price.toLocaleString()}
                          </p>
                          <p className="text-gray-400 tabular-nums">
                            지표값: {sig.value.toFixed(2)}
                          </p>
                        </div>
                      );
                    })
                  )}
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
                지표 선택
              </label>
              <div className="flex flex-wrap gap-2">
                {INDICATORS.map((ind) => (
                  <button
                    key={ind.id}
                    onClick={() => setSelectedIndicator(ind.id)}
                    className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                      selectedIndicator === ind.id
                        ? "bg-indigo-600 text-white border-indigo-600"
                        : "bg-white text-gray-700 border-gray-300 hover:border-indigo-400"
                    }`}
                  >
                    {ind.label}
                  </button>
                ))}
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

          {/* Content */}
          {loading ? (
            <Loading message="성공률 데이터 로딩 중..." />
          ) : error ? (
            <ErrorMessage message={error} onRetry={loadAccuracy} />
          ) : (
            <div className="space-y-6">
              {/* Accuracy bar chart + comparison */}
              <div className="grid grid-cols-4 gap-4">
                {/* Chart 3/4 */}
                <div className="col-span-3 space-y-4">
                  {/* Accuracy bar chart */}
                  {accuracyData.length > 0 && (
                    <div className="bg-white rounded-lg border border-gray-200 p-4">
                      <h3 className="text-sm font-semibold text-gray-700 mb-3">
                        {INDICATOR_LABELS[selectedIndicator] ?? selectedIndicator} 성공률 — {assetId} (T+{forwardDays}일)
                      </h3>
                      <AccuracyBarChart
                        data={accuracyData}
                        strategyLabels={INDICATOR_LABELS}
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
                                지표
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
                            {comparisonData.indicators.map((row) => (
                              <tr
                                key={row.strategy_id}
                                className="hover:bg-gray-50"
                              >
                                <td className="px-4 py-2 text-center font-semibold text-gray-700">
                                  {row.rank}
                                </td>
                                <td className="px-4 py-2 font-medium text-gray-700">
                                  {INDICATOR_LABELS[row.strategy_id] ??
                                    row.strategy_id}
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
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>

                {/* Trade detail table 1/4 */}
                <div className="col-span-1 bg-white rounded-lg border border-gray-200 p-4 space-y-4">
                  <h3 className="text-sm font-semibold text-gray-700">
                    지표별 요약
                  </h3>
                  {/* 성공률 기준 설명 (DI.6) */}
                  <div className="bg-gray-50 border border-gray-100 rounded p-2 text-xs text-gray-500 space-y-1">
                    <p>성공 기준: 매수 → T+{forwardDays}일 상승, 매도 → T+{forwardDays}일 하락</p>
                    <p>수익률: 시그널 T+{forwardDays}일 수익률 평균</p>
                  </div>
                  {accuracyData.map((acc) => (
                    <div
                      key={acc.strategy_id}
                      className="border border-gray-100 rounded p-3"
                    >
                      <h4 className="text-xs font-semibold text-gray-700 mb-2">
                        {INDICATOR_LABELS[acc.strategy_id] ?? acc.strategy_id}
                      </h4>
                      {acc.insufficient_data ? (
                        <p className="text-xs text-gray-400">
                          데이터 불충분 (시그널 {acc.total_signals}개)
                        </p>
                      ) : (
                        <div className="space-y-1 text-xs">
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
                            <span className="text-gray-500">매수 후 수익</span>
                            <span className="text-gray-700">
                              {fmtPct(acc.avg_return_after_buy)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">매도 후 수익</span>
                            <span className="text-gray-700">
                              {fmtPct(acc.avg_return_after_sell)}
                            </span>
                          </div>
                          <div className="pt-1 border-t border-gray-100 text-gray-400">
                            평가: {acc.evaluated_signals}/{acc.total_signals}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
