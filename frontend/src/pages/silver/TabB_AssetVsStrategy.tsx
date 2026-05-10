import { useState, useEffect } from "react";
import { fetchReplay, fetchStrategy } from "../../api/simulation";
import type { ReplayResponse, StrategyResponse } from "../../types/api";
import EquityChart from "./components/EquityChart";
import KpiCard from "./components/KpiCard";
import InterpretCard from "./components/InterpretCard";
import RiskCard from "./components/RiskCard";
import AssetPickerDrawer, { type AssetDef } from "./components/AssetPickerDrawer";
import { mergeEquityData, formatKRW, formatPct } from "./silverUtils";

const TAB_B_UNIVERSE: AssetDef[] = [
  { code: "QQQ", label: "QQQ (나스닥 100)", category: "US ETF" },
  { code: "SPY", label: "SPY (S&P 500)", category: "US ETF" },
  { code: "KS200", label: "KOSPI200", category: "KR 지수" },
];

const SERIES_KEYS = {
  plain: "단순 적립",
  stratA: "전략 A",
  stratB: "전략 B",
} as const;

type SeriesResult = {
  key: string;
  label: string;
  curve: ReplayResponse["curve"];
  kpi: ReplayResponse["kpi"];
};

type Props = {
  periodYears: 3 | 5 | 10;
  monthlyAmount: number;
};

export default function TabB_AssetVsStrategy({ periodYears, monthlyAmount }: Props) {
  const [selectedAsset, setSelectedAsset] = useState<string>("QQQ");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [series, setSeries] = useState<SeriesResult[]>([]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [plain, stratA, stratB] = await Promise.all([
          fetchReplay({ asset_code: selectedAsset, monthly_amount: monthlyAmount, period_years: periodYears }),
          fetchStrategy({ asset_code: selectedAsset, strategy: "A", monthly_amount: monthlyAmount, period_years: periodYears }),
          fetchStrategy({ asset_code: selectedAsset, strategy: "B", monthly_amount: monthlyAmount, period_years: periodYears }),
        ]);
        if (!cancelled) {
          setSeries([
            { key: SERIES_KEYS.plain, label: SERIES_KEYS.plain, curve: plain.curve, kpi: plain.kpi },
            { key: SERIES_KEYS.stratA, label: SERIES_KEYS.stratA, curve: (stratA as StrategyResponse).curve, kpi: (stratA as StrategyResponse).kpi },
            { key: SERIES_KEYS.stratB, label: SERIES_KEYS.stratB, curve: (stratB as StrategyResponse).curve, kpi: (stratB as StrategyResponse).kpi },
          ]);
        }
      } catch {
        if (!cancelled) setError("시뮬레이션 조회에 실패했습니다.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [selectedAsset, periodYears, monthlyAmount]);

  const chartData = mergeEquityData(
    series.map((s) => ({ key: s.key, curve: s.curve }))
  );

  const chartSeries = series.map((s) => ({ key: s.key, label: s.label }));

  const assetLabel =
    TAB_B_UNIVERSE.find((a) => a.code === selectedAsset)?.label ?? selectedAsset;

  const plainSeries = series.find((s) => s.key === SERIES_KEYS.plain);
  const bestStrategy = series
    .filter((s) => s.key !== SERIES_KEYS.plain)
    .reduce<SeriesResult | null>((best, s) => {
      if (!best || s.kpi.total_return > best.kpi.total_return) return s;
      return best;
    }, null);

  return (
    <div className="silver-tab-content">
      {/* 자산 선택 */}
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span className="silver-asset-tag">{selectedAsset}</span>
        <button
          className="silver-add-btn"
          onClick={() => setDrawerOpen(true)}
          type="button"
        >
          자산 변경
        </button>
      </div>

      {loading && <div className="silver-loading">시뮬레이션 중…</div>}
      {error && <div className="silver-error">{error}</div>}

      {!loading && series.length > 0 && (
        <>
          {/* 차트 */}
          <div className="silver-chart-card">
            <div
              style={{
                fontSize: 12,
                color: "var(--text-secondary)",
                fontWeight: 500,
                textTransform: "uppercase",
                letterSpacing: "0.04em",
                marginBottom: 12,
              }}
            >
              {selectedAsset} — 단순 적립 vs 전략 비교
            </div>
            <EquityChart data={chartData} series={chartSeries} />
          </div>

          {/* KPI 3열 비교 */}
          {series.map((s) => (
            <div key={s.key}>
              <div
                style={{
                  fontSize: 12,
                  color: "var(--text-secondary)",
                  fontWeight: 600,
                  marginBottom: 10,
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                }}
              >
                {s.label}
              </div>
              <div className="silver-kpi-grid">
                <KpiCard label="최종 자산" value={formatKRW(s.kpi.final_asset_krw)} />
                <KpiCard
                  label="총 수익률"
                  value={formatPct(s.kpi.total_return)}
                  delta={s.kpi.total_return}
                />
                <KpiCard
                  label="연환산 수익률"
                  value={formatPct(s.kpi.annualized_return)}
                  delta={s.kpi.annualized_return}
                />
                <KpiCard
                  label="최대 손실폭"
                  value={formatPct(s.kpi.yearly_worst_mdd)}
                  delta={s.kpi.yearly_worst_mdd}
                />
              </div>
            </div>
          ))}

          {/* 해석 — 전략 중 가장 좋은 것 */}
          {bestStrategy && (
            <InterpretCard
              assetLabel={`${assetLabel} · ${bestStrategy.label}`}
              periodYears={periodYears}
              monthlyAmount={monthlyAmount}
              kpi={bestStrategy.kpi}
            />
          )}

          {/* 리스크 — 단순 적립 MDD */}
          {plainSeries && (
            <RiskCard assetLabel={`${selectedAsset} 단순 적립`} kpi={plainSeries.kpi} />
          )}
        </>
      )}

      <AssetPickerDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        universe={TAB_B_UNIVERSE}
        selected={[selectedAsset]}
        onChange={(selected) => {
          if (selected.length > 0) setSelectedAsset(selected[selected.length - 1]);
          setDrawerOpen(false);
        }}
        maxSelect={1}
        title="자산 선택"
      />
    </div>
  );
}
