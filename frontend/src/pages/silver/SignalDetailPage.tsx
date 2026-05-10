import { useState, useEffect, useCallback } from "react";
import { fetchPrices } from "../../api/prices";
import { fetchFactors } from "../../api/factors";
import { fetchIndicatorSignals } from "../../api/analysis";
import type {
  PriceDailyResponse,
  FactorDailyResponse,
  IndicatorSignalItem,
} from "../../types/api";
import IndicatorOverlayChart from "../../components/charts/IndicatorOverlayChart";
import IndicatorCard from "./components/IndicatorCard";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const ASSETS = [
  { id: "QQQ", label: "QQQ (나스닥 100)" },
  { id: "SPY", label: "SPY (S&P 500)" },
  { id: "KS200", label: "KS200 (코스피200)" },
  { id: "NVDA", label: "NVDA (엔비디아)" },
  { id: "GOOGL", label: "GOOGL (알파벳)" },
  { id: "TSLA", label: "TSLA (테슬라)" },
  { id: "005930", label: "005930 (삼성전자)" },
  { id: "000660", label: "000660 (SK하이닉스)" },
] as const;

const INDICATORS = [
  { id: "rsi_14" as const, label: "RSI" },
  { id: "macd" as const, label: "MACD" },
  { id: "atr_vol" as const, label: "ATR" },
];

type IndicatorId = "rsi_14" | "macd" | "atr_vol";

const INDICATOR_FACTOR_MAP: Record<IndicatorId, string[]> = {
  rsi_14: ["rsi_14"],
  macd: ["macd", "macd_signal"],
  atr_vol: ["atr_14", "vol_20"],
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function defaultStart(): string {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 1);
  return d.toISOString().slice(0, 10);
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

type IndicatorStatus =
  | "과매수"
  | "과매도"
  | "중립"
  | "골든크로스"
  | "데드크로스"
  | "고변동"
  | "저변동";

interface CurrentIndicator {
  name: string;
  value: number;
  unit?: string;
  status: IndicatorStatus;
}

function computeCurrentIndicator(
  indicatorId: IndicatorId,
  factorData: Map<string, FactorDailyResponse[]>,
  prices: PriceDailyResponse[],
  assetId: string,
): CurrentIndicator | null {
  if (indicatorId === "rsi_14") {
    const records = factorData.get("rsi_14") ?? [];
    if (records.length === 0) return null;
    const value = records[records.length - 1].value;
    const status: IndicatorStatus =
      value > 70 ? "과매수" : value < 30 ? "과매도" : "중립";
    return { name: "RSI 14", value, status };
  }

  if (indicatorId === "macd") {
    const macdRecords = factorData.get("macd") ?? [];
    const signalRecords = factorData.get("macd_signal") ?? [];
    if (macdRecords.length === 0) return null;
    const latestMacd = macdRecords[macdRecords.length - 1];
    const latestSignal = signalRecords[signalRecords.length - 1];
    const histogram = latestMacd.value - (latestSignal?.value ?? 0);
    const status: IndicatorStatus = histogram >= 0 ? "골든크로스" : "데드크로스";
    return { name: "MACD 히스토그램", value: histogram, status };
  }

  if (indicatorId === "atr_vol") {
    const atrRecords = factorData.get("atr_14") ?? [];
    if (atrRecords.length === 0) return null;
    const latestAtr = atrRecords[atrRecords.length - 1];
    const latestPrice = prices
      .filter((p) => p.asset_id === assetId)
      .slice(-1)[0];
    const atrPct =
      latestPrice?.close && latestPrice.close > 0
        ? (latestAtr.value / latestPrice.close) * 100
        : latestAtr.value;
    const status: IndicatorStatus = atrPct > 3 ? "고변동" : "저변동";
    return { name: "ATR/가격", value: atrPct, unit: "%", status };
  }

  return null;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function SignalDetailPage() {
  const [assetId, setAssetId] = useState("QQQ");
  const [indicatorId, setIndicatorId] = useState<IndicatorId>("rsi_14");
  const [prices, setPrices] = useState<PriceDailyResponse[]>([]);
  const [factorData, setFactorData] = useState<
    Map<string, FactorDailyResponse[]>
  >(new Map());
  const [signalDates, setSignalDates] = useState<IndicatorSignalItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const start = defaultStart();
    const end = today();
    const factorNames = INDICATOR_FACTOR_MAP[indicatorId];
    try {
      const [priceData, signalData, ...factorResults] = await Promise.all([
        fetchPrices({
          asset_id: assetId,
          start_date: start,
          end_date: end,
          limit: 500,
        }),
        fetchIndicatorSignals({
          asset_id: assetId,
          indicator_id: indicatorId,
          start_date: start,
          end_date: end,
        }),
        ...factorNames.map((name) =>
          fetchFactors({
            asset_id: assetId,
            factor_name: name,
            start_date: start,
            end_date: end,
            limit: 500,
          }),
        ),
      ]);
      setPrices(priceData);
      setSignalDates(signalData.signals);
      const newMap = new Map<string, FactorDailyResponse[]>();
      factorNames.forEach((name, i) => newMap.set(name, factorResults[i]));
      setFactorData(newMap);
    } catch (err) {
      setError(err instanceof Error ? err.message : "데이터 로딩 실패");
    } finally {
      setLoading(false);
    }
  }, [assetId, indicatorId]);

  useEffect(() => {
    load();
  }, [load]);

  const currentIndicator = computeCurrentIndicator(
    indicatorId,
    factorData,
    prices,
    assetId,
  );
  const assetLabel = ASSETS.find((a) => a.id === assetId)?.label ?? assetId;
  const indicatorLabel =
    INDICATORS.find((i) => i.id === indicatorId)?.label ?? indicatorId;

  return (
    <div className="silver-section">
      {/* Header */}
      <div>
        <h2
          style={{
            color: "var(--text-primary)",
            fontSize: 20,
            fontWeight: 600,
            marginBottom: 4,
          }}
        >
          신호 상세
        </h2>
        <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>
          RSI · MACD · ATR 현재 지표 상태 및 차트 (최근 1년)
        </p>
      </div>

      {/* Controls */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 16,
          flexWrap: "wrap",
        }}
      >
        {/* 자산 선택 (8종 고정) */}
        <select
          value={assetId}
          onChange={(e) => setAssetId(e.target.value)}
          style={{
            background: "var(--bg-card)",
            color: "var(--text-primary)",
            border: "1px solid var(--border-card)",
            borderRadius: 8,
            padding: "8px 12px",
            fontSize: 14,
            cursor: "pointer",
            outline: "none",
            minWidth: 200,
          }}
        >
          {ASSETS.map((a) => (
            <option key={a.id} value={a.id}>
              {a.label}
            </option>
          ))}
        </select>

        {/* 지표 탭 (RSI / MACD / ATR) */}
        <div className="silver-pill-group">
          {INDICATORS.map((ind) => (
            <button
              key={ind.id}
              className={`silver-pill${indicatorId === ind.id ? " silver-pill--active" : ""}`}
              onClick={() => setIndicatorId(ind.id)}
            >
              {ind.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "48px 0",
          }}
        >
          <p style={{ color: "var(--text-secondary)", fontSize: 14 }}>
            로딩 중...
          </p>
        </div>
      ) : error ? (
        <div
          className="silver-card"
          style={{ textAlign: "center", padding: "32px 20px" }}
        >
          <p
            style={{
              color: "var(--accent-red)",
              fontSize: 14,
              marginBottom: 12,
            }}
          >
            {error}
          </p>
          <button
            onClick={load}
            style={{
              background: "var(--bg-pill-active)",
              color: "var(--text-primary)",
              border: "1px solid var(--border-card)",
              borderRadius: 8,
              padding: "8px 16px",
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            다시 시도
          </button>
        </div>
      ) : (
        <div
          style={{
            display: "flex",
            gap: 16,
            alignItems: "flex-start",
            flexWrap: "wrap",
          }}
        >
          {/* IndicatorCard — 현재 지표값 + 상태 라벨 */}
          <div style={{ minWidth: 220, maxWidth: 260, flexShrink: 0 }}>
            {currentIndicator ? (
              <IndicatorCard
                assetLabel={assetLabel}
                indicators={[currentIndicator]}
              />
            ) : (
              <div className="silver-card">
                <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>
                  지표 데이터 없음
                </p>
              </div>
            )}
          </div>

          {/* IndicatorOverlayChart — 가격 + 지표 overlay */}
          <div className="silver-card" style={{ flex: 1, minWidth: 0 }}>
            <div style={{ marginBottom: 12 }}>
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 500,
                  color: "var(--text-secondary)",
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                }}
              >
                {assetId} — {indicatorLabel} 차트
              </span>
            </div>
            <IndicatorOverlayChart
              prices={prices}
              factors={factorData}
              assetId={assetId}
              selectedFactors={INDICATOR_FACTOR_MAP[indicatorId]}
              signalDates={signalDates}
              indicatorId={indicatorId}
            />
          </div>
        </div>
      )}
    </div>
  );
}
