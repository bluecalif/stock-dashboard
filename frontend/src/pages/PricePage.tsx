import { useState, useEffect, useCallback } from "react";
import { fetchPrices } from "../api/prices";
import type { PriceDailyResponse } from "../types/api";
import type { PricePoint } from "../components/charts/PriceLineChart";
import type { ReturnsPoint } from "../components/charts/ReturnsChart";
import PriceLineChart from "../components/charts/PriceLineChart";
import ReturnsChart from "../components/charts/ReturnsChart";
import AssetSelect from "../components/common/AssetSelect";
import DateRangePicker from "../components/common/DateRangePicker";
import Loading from "../components/common/Loading";
import ErrorMessage from "../components/common/ErrorMessage";

type ViewMode = "price" | "returns";

function defaultStart(): string {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 1);
  return d.toISOString().slice(0, 10);
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

/** 여러 자산의 PriceDailyResponse[]를 date 기준으로 병합 (종가) */
function mergeByDate(
  allPrices: Map<string, PriceDailyResponse[]>,
): PricePoint[] {
  const dateMap = new Map<string, PricePoint>();

  for (const [assetId, prices] of allPrices) {
    for (const p of prices) {
      const existing = dateMap.get(p.date);
      if (existing) {
        existing[assetId] = p.close;
      } else {
        dateMap.set(p.date, { date: p.date, [assetId]: p.close });
      }
    }
  }

  return Array.from(dateMap.values()).sort((a, b) =>
    a.date.localeCompare(b.date),
  );
}

/** 종가 → 정규화 누적수익률(기준일=100)로 변환 */
function toNormalizedReturns(
  allPrices: Map<string, PriceDailyResponse[]>,
): ReturnsPoint[] {
  // 각 자산의 첫 종가를 기준값으로 저장
  const basePrice = new Map<string, number>();
  for (const [assetId, prices] of allPrices) {
    if (prices.length > 0) {
      basePrice.set(assetId, prices[0].close);
    }
  }

  const dateMap = new Map<string, ReturnsPoint>();

  for (const [assetId, prices] of allPrices) {
    const base = basePrice.get(assetId);
    if (!base) continue;
    for (const p of prices) {
      const normalized = (p.close / base) * 100;
      const existing = dateMap.get(p.date);
      if (existing) {
        existing[assetId] = normalized;
      } else {
        dateMap.set(p.date, { date: p.date, [assetId]: normalized });
      }
    }
  }

  return Array.from(dateMap.values()).sort((a, b) =>
    a.date.localeCompare(b.date),
  );
}

export default function PricePage() {
  const [viewMode, setViewMode] = useState<ViewMode>("price");
  const [selectedIds, setSelectedIds] = useState<string[]>(["KS200"]);
  const [startDate, setStartDate] = useState(defaultStart);
  const [endDate, setEndDate] = useState(today);
  const [priceMap, setPriceMap] = useState<Map<string, PriceDailyResponse[]>>(
    new Map(),
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPrices = useCallback(async () => {
    if (selectedIds.length === 0) {
      setPriceMap(new Map());
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const results = await Promise.all(
        selectedIds.map((id) =>
          fetchPrices({
            asset_id: id,
            start_date: startDate,
            end_date: endDate,
          }),
        ),
      );
      const map = new Map<string, PriceDailyResponse[]>();
      selectedIds.forEach((id, i) => map.set(id, results[i]));
      setPriceMap(map);
    } catch (err) {
      setError(err instanceof Error ? err.message : "데이터 로딩 실패");
    } finally {
      setLoading(false);
    }
  }, [selectedIds, startDate, endDate]);

  useEffect(() => {
    loadPrices();
  }, [loadPrices]);

  const chartData = mergeByDate(priceMap);
  const returnsData = toNormalizedReturns(priceMap);

  const tabs: { key: ViewMode; label: string }[] = [
    { key: "price", label: "가격" },
    { key: "returns", label: "수익률 비교" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">가격 차트</h2>
        <p className="text-gray-500 mt-1 text-sm">
          자산별 종가 라인 차트 · 정규화 수익률 비교
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

      {/* 탭 + 차트 영역 */}
      <div className="bg-white rounded-lg border border-gray-200">
        {/* 탭 */}
        <div className="flex border-b border-gray-200">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setViewMode(tab.key)}
              className={`px-4 py-2.5 text-sm font-medium transition-colors ${
                viewMode === tab.key
                  ? "text-blue-600 border-b-2 border-blue-600"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* 차트 */}
        <div className="p-4">
          {loading ? (
            <Loading message="가격 데이터 로딩 중..." />
          ) : error ? (
            <ErrorMessage message={error} onRetry={loadPrices} />
          ) : viewMode === "price" ? (
            <PriceLineChart data={chartData} assetIds={selectedIds} />
          ) : (
            <ReturnsChart data={returnsData} assetIds={selectedIds} />
          )}
        </div>
      </div>
    </div>
  );
}
