import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from "recharts";
import type {
  PriceDailyResponse,
  FactorDailyResponse,
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

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatPrice(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return value.toLocaleString();
  return value.toFixed(2);
}

/** Min-max 정규화 → 0~100 */
function minMaxNormalize(values: number[]): number[] {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  return values.map((v) => ((v - min) / range) * 100);
}

/** % 변화: 시작점 대비 변화율 */
function pctChange(values: number[]): number[] {
  const base = values[0] || 1;
  return values.map((v) => ((v - base) / Math.abs(base)) * 100);
}

function mergeRawData(
  prices: PriceDailyResponse[],
  factors: Map<string, FactorDailyResponse[]>,
  assetId: string,
  selectedFactors: string[],
): ChartPoint[] {
  const dateMap = new Map<string, ChartPoint>();

  for (const p of prices) {
    if (p.asset_id !== assetId) continue;
    dateMap.set(p.date, { date: p.date, close: p.close });
  }

  for (const factorName of selectedFactors) {
    const records = factors.get(factorName) || [];
    for (const r of records) {
      if (r.asset_id !== assetId) continue;
      const existing = dateMap.get(r.date);
      if (existing) {
        existing[factorName] = r.value;
      } else {
        dateMap.set(r.date, { date: r.date, [factorName]: r.value });
      }
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

  const priceValues = raw.map((p) => (p.close as number) ?? 0);
  const priceTransformed = transform(priceValues);

  const factorTransformed = new Map<string, number[]>();
  for (const f of selectedFactors) {
    const vals = raw.map((p) => (p[f] as number) ?? 0);
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

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function IndicatorOverlayChart({
  prices,
  factors,
  assetId,
  selectedFactors,
  normalizeMode = "raw",
}: Props) {
  if (prices.length === 0) {
    return (
      <div className="flex items-center justify-center h-80 text-gray-400">
        데이터가 없습니다
      </div>
    );
  }

  const raw = mergeRawData(prices, factors, assetId, selectedFactors);
  const data = applyTransform(raw, selectedFactors, normalizeMode);
  const isTransformed = normalizeMode !== "raw";
  const hasRSI = selectedFactors.includes("rsi_14");
  const showDualAxis = !isTransformed && selectedFactors.length > 0;

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
