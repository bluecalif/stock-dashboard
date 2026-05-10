import { useState, useEffect } from "react";
import { fetchReplay } from "../../api/simulation";
import type { ReplayResponse } from "../../types/api";
import EquityChart, { SERIES_COLORS } from "./components/EquityChart";
import InterpretCard from "./components/InterpretCard";
import RiskCard from "./components/RiskCard";
import AssetPickerDrawer, { type AssetDef } from "./components/AssetPickerDrawer";
import { mergeEquityData, formatKRW, formatPct } from "./silverUtils";

const TAB_A_UNIVERSE: AssetDef[] = [
  { code: "QQQ", label: "QQQ (나스닥 100)", category: "US ETF" },
  { code: "SPY", label: "SPY (S&P 500)", category: "US ETF" },
  { code: "SCHD", label: "SCHD (배당 성장)", category: "US ETF" },
  { code: "JEPI", label: "JEPI (커버드콜)", category: "US ETF" },
  { code: "KS200", label: "KOSPI200", category: "KR 지수" },
  { code: "WBI", label: "WBI (워런 버핏 지수)", category: "벤치마크" },
];

type Props = {
  periodYears: 3 | 5 | 10;
  monthlyAmount: number;
};

export default function TabA_SingleAsset({ periodYears, monthlyAmount }: Props) {
  const [selectedAssets, setSelectedAssets] = useState<string[]>(["QQQ", "SPY", "KS200"]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ReplayResponse[]>([]);

  useEffect(() => {
    if (selectedAssets.length === 0) return;
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await Promise.all(
          selectedAssets.map((asset_code) =>
            fetchReplay({ asset_code, monthly_amount: monthlyAmount, period_years: periodYears })
          )
        );
        if (!cancelled) setResults(data);
      } catch {
        if (!cancelled) setError("시뮬레이션 조회에 실패했습니다.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [selectedAssets, periodYears, monthlyAmount]);

  const chartData = mergeEquityData(
    results.map((r) => ({ key: r.asset_code, curve: r.curve }))
  );

  const series = results.map((r) => ({ key: r.asset_code, label: r.asset_code }));

  const assetLabelMap = Object.fromEntries(
    TAB_A_UNIVERSE.map((a) => [a.code, a.label])
  );

  const bestResult = results.reduce<ReplayResponse | null>((best, r) => {
    if (!best || r.kpi.total_return > best.kpi.total_return) return r;
    return best;
  }, null);

  const worstMddResult = results.reduce<ReplayResponse | null>((worst, r) => {
    if (!worst || r.kpi.yearly_worst_mdd < worst.kpi.yearly_worst_mdd) return r;
    return worst;
  }, null);

  return (
    <div className="silver-tab-content">
      {/* 자산 선택 바 */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        {selectedAssets.map((code) => (
          <span key={code} className="silver-asset-tag">
            {code}
            <button
              className="silver-asset-tag__remove"
              onClick={() => setSelectedAssets((prev) => prev.filter((c) => c !== code))}
              aria-label={`${code} 제거`}
              type="button"
            >
              ×
            </button>
          </span>
        ))}
        <button
          className="silver-add-btn"
          onClick={() => setDrawerOpen(true)}
          type="button"
        >
          + 자산 추가
        </button>
      </div>

      {loading && <div className="silver-loading">시뮬레이션 중…</div>}
      {error && <div className="silver-error">{error}</div>}

      {!loading && results.length > 0 && (
        <>
          {/* 누적 자산 차트 */}
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
              누적 자산가치 (KRW)
            </div>
            <EquityChart data={chartData} series={series} />
          </div>

          {/* 비교 테이블 */}
          <div className="silver-compare-table">
            <table>
              <thead>
                <tr>
                  <th>자산</th>
                  <th>최종 자산</th>
                  <th>총 수익률</th>
                  <th>연환산</th>
                  <th>최대 손실폭</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r, i) => (
                  <tr key={r.asset_code}>
                    <td>
                      <span
                        style={{
                          display: "inline-block",
                          width: 10,
                          height: 10,
                          borderRadius: "50%",
                          background: SERIES_COLORS[i % SERIES_COLORS.length],
                          marginRight: 8,
                        }}
                      />
                      {r.asset_code}
                    </td>
                    <td>{formatKRW(r.kpi.final_asset_krw)}</td>
                    <td className={r.kpi.total_return >= 0 ? "positive" : "negative"}>
                      {formatPct(r.kpi.total_return)}
                    </td>
                    <td className={r.kpi.annualized_return >= 0 ? "positive" : "negative"}>
                      {formatPct(r.kpi.annualized_return)}
                    </td>
                    <td className="negative">
                      {formatPct(r.kpi.yearly_worst_mdd)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 베스트 자산 해석 카드 */}
          {bestResult && (
            <InterpretCard
              assetLabel={assetLabelMap[bestResult.asset_code] ?? bestResult.asset_code}
              periodYears={periodYears}
              monthlyAmount={monthlyAmount}
              kpi={bestResult.kpi}
            />
          )}

          {/* 최대 손실폭 리스크 카드 */}
          {worstMddResult && (
            <RiskCard
              assetLabel={assetLabelMap[worstMddResult.asset_code] ?? worstMddResult.asset_code}
              kpi={worstMddResult.kpi}
            />
          )}
        </>
      )}

      <AssetPickerDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        universe={TAB_A_UNIVERSE}
        selected={selectedAssets}
        onChange={setSelectedAssets}
        maxSelect={6}
        title="자산 선택 (최대 6종)"
      />
    </div>
  );
}
