import { useState, useEffect } from "react";
import { fetchReplay, fetchPortfolio } from "../../api/simulation";
import type { ReplayResponse, PortfolioResponse } from "../../types/api";
import EquityChart from "./components/EquityChart";
import KpiCard from "./components/KpiCard";
import InterpretCard from "./components/InterpretCard";
import RiskCard from "./components/RiskCard";
import PillGroup from "./components/PillGroup";
import { mergeEquityData, formatKRW, formatPct } from "./silverUtils";

const PRESETS = [
  {
    key: "QQQ_TLT_BTC",
    label: "QQQ + TLT + BTC",
    sub: "60 / 20 / 20",
    primaryAsset: "QQQ",
    primaryLabel: "QQQ",
  },
  {
    key: "KS200_TLT_BTC",
    label: "KS200 + TLT + BTC",
    sub: "60 / 20 / 20",
    primaryAsset: "KS200",
    primaryLabel: "KS200",
  },
  {
    key: "TECH_TLT_BTC",
    label: "테크 + TLT + BTC",
    sub: "60 / 20 / 20",
    primaryAsset: "QQQ",
    primaryLabel: "QQQ (대리)",
  },
  {
    key: "SEC_SKH_TLT_BTC",
    label: "삼성+하이닉스 + TLT + BTC",
    sub: "30 / 30 / 20 / 20",
    primaryAsset: "005930",
    primaryLabel: "삼성전자",
  },
];

const PRESET_PILL_OPTIONS = PRESETS.map((p) => ({
  value: p.key,
  label: p.label,
}));

type Props = {
  periodYears: 3 | 5 | 10;
  monthlyAmount: number;
};

export default function TabC_AssetVsPortfolio({ periodYears, monthlyAmount }: Props) {
  const [presetKey, setPresetKey] = useState<string>("QQQ_TLT_BTC");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [replayResult, setReplayResult] = useState<ReplayResponse | null>(null);
  const [portfolioResult, setPortfolioResult] = useState<PortfolioResponse | null>(null);

  const preset = PRESETS.find((p) => p.key === presetKey) ?? PRESETS[0];

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [replay, portfolio] = await Promise.all([
          fetchReplay({
            asset_code: preset.primaryAsset,
            monthly_amount: monthlyAmount,
            period_years: periodYears,
          }),
          fetchPortfolio({
            preset_key: presetKey,
            monthly_amount: monthlyAmount,
            period_years: periodYears,
          }),
        ]);
        if (!cancelled) {
          setReplayResult(replay);
          setPortfolioResult(portfolio);
        }
      } catch {
        if (!cancelled) setError("시뮬레이션 조회에 실패했습니다.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [presetKey, periodYears, monthlyAmount, preset.primaryAsset]);

  const chartData =
    replayResult && portfolioResult
      ? mergeEquityData([
          { key: preset.primaryLabel, curve: replayResult.curve },
          { key: "포트폴리오", curve: portfolioResult.curve },
        ])
      : [];

  const chartSeries = [
    { key: preset.primaryLabel, label: preset.primaryLabel },
    { key: "포트폴리오", label: portfolioResult?.preset_name ?? "포트폴리오" },
  ];

  return (
    <div className="silver-tab-content">
      {/* 프리셋 선택 */}
      <div style={{ overflowX: "auto", paddingBottom: 4 }}>
        <PillGroup
          options={PRESET_PILL_OPTIONS}
          value={presetKey}
          onChange={setPresetKey}
          ariaLabel="포트폴리오 프리셋 선택"
        />
      </div>

      {/* 비중 표시 */}
      <div style={{ fontSize: 13, color: "var(--text-tertiary)" }}>
        {preset.label} · 비중 {preset.sub}
        {preset.primaryAsset !== preset.primaryLabel && (
          <span style={{ marginLeft: 8 }}>
            (비교 자산: {preset.primaryLabel} 근사치)
          </span>
        )}
      </div>

      {loading && <div className="silver-loading">시뮬레이션 중…</div>}
      {error && <div className="silver-error">{error}</div>}

      {!loading && replayResult && portfolioResult && (
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
              {preset.primaryLabel} 단순 적립 vs {portfolioResult.preset_name}
            </div>
            <EquityChart data={chartData} series={chartSeries} />
          </div>

          {/* KPI 비교 — 2행 */}
          {[
            { label: preset.primaryLabel, kpi: replayResult.kpi },
            { label: portfolioResult.preset_name, kpi: portfolioResult.kpi },
          ].map((item) => (
            <div key={item.label}>
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
                {item.label}
              </div>
              <div className="silver-kpi-grid">
                <KpiCard label="최종 자산" value={formatKRW(item.kpi.final_asset_krw)} />
                <KpiCard
                  label="총 수익률"
                  value={formatPct(item.kpi.total_return)}
                  delta={item.kpi.total_return}
                />
                <KpiCard
                  label="연환산 수익률"
                  value={formatPct(item.kpi.annualized_return)}
                  delta={item.kpi.annualized_return}
                />
                <KpiCard
                  label="최대 손실폭"
                  value={formatPct(item.kpi.yearly_worst_mdd)}
                  delta={item.kpi.yearly_worst_mdd}
                />
              </div>
            </div>
          ))}

          {/* 포트폴리오 해석 카드 */}
          <InterpretCard
            assetLabel={portfolioResult.preset_name}
            periodYears={periodYears}
            monthlyAmount={monthlyAmount}
            kpi={portfolioResult.kpi}
          />

          {/* 단순 자산 리스크 카드 */}
          <RiskCard assetLabel={preset.primaryLabel} kpi={replayResult.kpi} />
        </>
      )}
    </div>
  );
}
