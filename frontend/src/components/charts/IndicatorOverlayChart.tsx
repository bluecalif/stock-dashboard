import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
  ReferenceArea,
} from "recharts";
import type {
  PriceDailyResponse,
  FactorDailyResponse,
  IndicatorSignalItem,
} from "../../types/api";
import { getFactorLabel } from "./FactorChart";
import type { NormalizeMode } from "../common/IndicatorSettingsPanel";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Props {
  prices: PriceDailyResponse[];
  factors: Map<string, FactorDailyResponse[]>;
  assetId: string;
  selectedFactors: string[];
  normalizeMode?: NormalizeMode;
  /** DR.6: signal dates for vertical reference lines */
  signalDates?: IndicatorSignalItem[];
  /** DR.9: indicator ID to apply special rendering */
  indicatorId?: string;
}

interface ChartPoint {
  date: string;
  close?: number;
  [key: string]: number | string | undefined;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PRICE_COLOR = "#2563eb";
const FACTOR_COLORS = [
  "#dc2626",
  "#16a34a",
  "#9333ea",
  "#ea580c",
  "#0891b2",
  "#db2777",
];

const RSI_REFS = [
  { y: 70, color: "#ef4444", label: "70" },
  { y: 30, color: "#3b82f6", label: "30" },
];

const SIGNAL_COLORS: Record<number, string> = {
  1: "#16a34a",   // buy — green
  [-1]: "#dc2626", // sell — red
  2: "#2563eb",   // buy exit — blue
  [-2]: "#ea580c", // sell exit — orange
  0: "#d97706",   // warning — amber
};

const SIGNAL_MARKER: Record<number, string> = {
  1: "B",
  [-1]: "S",
  2: "X",
  [-2]: "X",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatPrice(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return value.toLocaleString();
  return value.toFixed(2);
}

/** Min-max normalize → 0~100 (DR.8: filter out undefined) */
function minMaxNormalize(values: (number | undefined)[]): (number | undefined)[] {
  const valid = values.filter((v): v is number => v !== undefined);
  if (valid.length === 0) return values.map(() => undefined);
  const min = Math.min(...valid);
  const max = Math.max(...valid);
  const range = max - min || 1;
  return values.map((v) => (v !== undefined ? ((v - min) / range) * 100 : undefined));
}

/** % change from start (DR.8: filter out undefined) */
function pctChange(values: (number | undefined)[]): (number | undefined)[] {
  const firstValid = values.find((v): v is number => v !== undefined);
  if (firstValid === undefined) return values.map(() => undefined);
  const base = firstValid || 1;
  return values.map((v) =>
    v !== undefined ? ((v - base) / Math.abs(base)) * 100 : undefined,
  );
}

/** DR.8: Merge raw data — exclude points where close is missing */
function mergeRawData(
  prices: PriceDailyResponse[],
  factors: Map<string, FactorDailyResponse[]>,
  assetId: string,
  selectedFactors: string[],
  indicatorId?: string,
): ChartPoint[] {
  const dateMap = new Map<string, ChartPoint>();

  for (const p of prices) {
    if (p.asset_id !== assetId) continue;
    if (p.close == null) continue; // DR.8: skip null/0 prices
    dateMap.set(p.date, { date: p.date, close: p.close });
  }

  for (const factorName of selectedFactors) {
    const records = factors.get(factorName) || [];
    for (const r of records) {
      if (r.asset_id !== assetId) continue;
      const existing = dateMap.get(r.date);
      if (existing) {
        let val = r.value;
        // DI.4: ATR+vol → convert to % scale
        if (indicatorId === "atr_vol") {
          if (factorName === "atr_14" && existing.close && existing.close > 0) {
            val = (val / existing.close) * 100; // atr_pct %
          } else if (factorName === "vol_20") {
            val = val * 100; // annualized vol %
          }
        }
        existing[factorName] = val;
      }
      // DR.8: Don't create entries for dates without price data
    }
  }

  return Array.from(dateMap.values()).sort((a, b) =>
    a.date.localeCompare(b.date),
  );
}

function applyTransform(
  raw: ChartPoint[],
  selectedFactors: string[],
  mode: NormalizeMode,
): ChartPoint[] {
  if (mode === "raw") return raw;

  const transform = mode === "normalized" ? minMaxNormalize : pctChange;

  // DR.8: use undefined instead of 0 for missing values
  const priceValues = raw.map((p) => p.close);
  const priceTransformed = transform(priceValues);

  const factorTransformed = new Map<string, (number | undefined)[]>();
  for (const f of selectedFactors) {
    const vals = raw.map((p) => p[f] as number | undefined);
    factorTransformed.set(f, transform(vals));
  }

  return raw.map((point, i) => {
    const result: ChartPoint = { date: point.date };
    result.close = priceTransformed[i];
    for (const f of selectedFactors) {
      result[f] = factorTransformed.get(f)?.[i];
    }
    return result;
  });
}

/** DR.9: Compute ATR high-volatility zones for ReferenceArea */
function computeAtrZones(
  signals: IndicatorSignalItem[],
): Array<{ x1: string; x2: string }> {
  const zones: Array<{ x1: string; x2: string }> = [];
  let zoneStart: string | null = null;

  for (const sig of signals) {
    if (sig.label.includes("진입")) {
      zoneStart = sig.date;
    } else if (sig.label.includes("복귀") && zoneStart) {
      zones.push({ x1: zoneStart, x2: sig.date });
      zoneStart = null;
    }
  }
  // If still in a zone at the end, extend to last signal
  if (zoneStart && signals.length > 0) {
    zones.push({ x1: zoneStart, x2: signals[signals.length - 1].date });
  }
  return zones;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function IndicatorOverlayChart({
  prices,
  factors,
  assetId,
  selectedFactors,
  normalizeMode = "raw",
  signalDates,
  indicatorId,
}: Props) {
  if (prices.length === 0) {
    return (
      <div className="flex items-center justify-center h-80 text-gray-400">
        데이터가 없습니다
      </div>
    );
  }

  const raw = mergeRawData(prices, factors, assetId, selectedFactors, indicatorId);
  const data = applyTransform(raw, selectedFactors, normalizeMode);
  const isTransformed = normalizeMode !== "raw";
  const hasRSI = selectedFactors.includes("rsi_14");
  const showDualAxis = !isTransformed && selectedFactors.length > 0;

  // DR.9: ATR zones
  const isAtr = indicatorId === "atr_vol";
  const atrZones = isAtr && signalDates ? computeAtrZones(signalDates) : [];

  // DR.6 + DI.3: Buy/sell/exit signal lines (non-ATR)
  const signalLines =
    signalDates && !isAtr
      ? signalDates.filter((s) => s.signal !== 0)
      : [];

  const yLabel =
    normalizeMode === "normalized"
      ? "정규화 (0~100)"
      : normalizeMode === "percent"
        ? "% 변화"
        : "";

  const yDomain: [number | string, number | string] =
    normalizeMode === "normalized" ? [0, 100] : ["auto", "auto"];

  const yFormatter =
    normalizeMode === "raw"
      ? formatPrice
      : (v: number) =>
          normalizeMode === "percent" ? `${v.toFixed(0)}%` : v.toFixed(0);

  return (
    <ResponsiveContainer width="100%" height={420}>
      <ComposedChart data={data}>
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11 }}
          tickFormatter={(v: string) => v.slice(5)}
        />

        {/* Left Y-axis */}
        <YAxis
          yAxisId="price"
          tick={{ fontSize: 11 }}
          tickFormatter={yFormatter}
          width={70}
          domain={yDomain}
          label={
            yLabel
              ? {
                  value: yLabel,
                  angle: -90,
                  position: "insideLeft",
                  fontSize: 10,
                  fill: "#9ca3af",
                }
              : undefined
          }
        />

        {/* Right Y-axis (raw mode only) */}
        {showDualAxis && (
          <YAxis
            yAxisId="indicator"
            orientation="right"
            tick={{ fontSize: 11 }}
            width={50}
            domain={
              hasRSI && selectedFactors.length === 1
                ? [0, 100]
                : ["auto", "auto"]
            }
          />
        )}

        <Tooltip
          labelFormatter={(label: string) => label}
          formatter={(value: number, name: string) => {
            if (isTransformed) {
              const suffix = normalizeMode === "percent" ? "%" : "";
              const label =
                name === "종가" ? name : getFactorLabel(name);
              return [`${value.toFixed(1)}${suffix}`, label];
            }
            if (name === "종가") return [formatPrice(value), name];
            return [value.toFixed(4), getFactorLabel(name)];
          }}
        />
        <Legend />

        {/* RSI reference lines (raw mode, single factor) */}
        {hasRSI &&
          !isTransformed &&
          selectedFactors.length === 1 &&
          RSI_REFS.map((ref) => (
            <ReferenceLine
              key={ref.y}
              yAxisId="indicator"
              y={ref.y}
              stroke={ref.color}
              strokeDasharray="4 4"
            />
          ))}

        {/* Zero line for percent mode */}
        {normalizeMode === "percent" && (
          <ReferenceLine
            yAxisId="price"
            y={0}
            stroke="#9ca3af"
            strokeDasharray="4 4"
          />
        )}

        {/* DI.4: ATR reference lines (3% / 30%) */}
        {isAtr && showDualAxis && (
          <>
            <ReferenceLine
              yAxisId="indicator"
              y={3}
              stroke="#ef4444"
              strokeDasharray="4 4"
              label={{ value: "ATR 3%", position: "right", fontSize: 9, fill: "#ef4444" }}
            />
            <ReferenceLine
              yAxisId="indicator"
              y={30}
              stroke="#f97316"
              strokeDasharray="4 4"
              label={{ value: "Vol 30%", position: "right", fontSize: 9, fill: "#f97316" }}
            />
          </>
        )}

        {/* DR.9: ATR high-volatility zones */}
        {atrZones.map((zone, i) => (
          <ReferenceArea
            key={`atr-zone-${i}`}
            yAxisId="price"
            x1={zone.x1}
            x2={zone.x2}
            fill="#dc2626"
            fillOpacity={0.08}
            stroke="#dc2626"
            strokeOpacity={0.2}
          />
        ))}

        {/* DR.6 + DI.3: Signal vertical reference lines */}
        {signalLines.map((sig, i) => {
          const isExit = sig.signal === 2 || sig.signal === -2;
          const color = SIGNAL_COLORS[sig.signal] ?? "#9ca3af";
          return (
            <ReferenceLine
              key={`sig-${i}`}
              yAxisId="price"
              x={sig.date}
              stroke={color}
              strokeDasharray={isExit ? "2 4" : undefined}
              strokeWidth={isExit ? 1 : 2}
              strokeOpacity={isExit ? 0.6 : 1}
              label={{
                value: SIGNAL_MARKER[sig.signal] ?? "?",
                position: "top",
                fontSize: isExit ? 9 : 12,
                fill: color,
                opacity: isExit ? 0.6 : 1,
              }}
            />
          );
        })}

        {/* Price line */}
        <Line
          yAxisId="price"
          type="monotone"
          dataKey="close"
          name="종가"
          stroke={PRICE_COLOR}
          dot={false}
          strokeWidth={2}
          connectNulls
        />

        {/* Factor lines */}
        {selectedFactors.map((f, i) => (
          <Line
            key={f}
            yAxisId={isTransformed ? "price" : "indicator"}
            type="monotone"
            dataKey={f}
            name={f}
            stroke={FACTOR_COLORS[i % FACTOR_COLORS.length]}
            dot={false}
            strokeWidth={1.5}
            connectNulls
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
