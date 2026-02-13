import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
  Bar,
  ComposedChart,
} from "recharts";
import type { FactorDailyResponse } from "../../types/api";

interface Props {
  data: FactorDailyResponse[];
  factorName: string;
  assetIds: string[];
}

const COLORS = [
  "#2563eb",
  "#dc2626",
  "#16a34a",
  "#9333ea",
  "#ea580c",
  "#0891b2",
  "#db2777",
];

interface ChartPoint {
  date: string;
  [key: string]: number | string;
}

/** 팩터 데이터를 date 기준으로 병합 */
function mergeFactorByDate(
  data: FactorDailyResponse[],
  assetIds: string[],
): ChartPoint[] {
  const dateMap = new Map<string, ChartPoint>();

  for (const d of data) {
    if (!assetIds.includes(d.asset_id)) continue;
    const existing = dateMap.get(d.date);
    if (existing) {
      existing[d.asset_id] = d.value;
    } else {
      dateMap.set(d.date, { date: d.date, [d.asset_id]: d.value });
    }
  }

  return Array.from(dateMap.values()).sort((a, b) =>
    a.date.localeCompare(b.date),
  );
}

/** MACD 데이터를 위해 macd + ema_12 + ema_26 데이터 병합 (단일 자산) */
function mergeMacdData(
  macdData: FactorDailyResponse[],
  signalData: FactorDailyResponse[],
  assetId: string,
): ChartPoint[] {
  const dateMap = new Map<string, ChartPoint>();

  for (const d of macdData) {
    if (d.asset_id !== assetId) continue;
    dateMap.set(d.date, { date: d.date, macd: d.value });
  }

  for (const d of signalData) {
    if (d.asset_id !== assetId) continue;
    const existing = dateMap.get(d.date);
    if (existing) {
      existing["signal"] = d.value;
    }
  }

  // MACD 히스토그램 계산
  const points = Array.from(dateMap.values()).sort((a, b) =>
    a.date.localeCompare(b.date),
  );
  for (const p of points) {
    if (typeof p.macd === "number" && typeof p.signal === "number") {
      p["histogram"] = p.macd - p.signal;
    }
  }

  return points;
}

/** RSI 서브차트 — 70/30 기준선 */
function RSIChart({ data, assetIds }: { data: ChartPoint[]; assetIds: string[] }) {
  if (data.length === 0) {
    return <EmptyState />;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11 }}
          tickFormatter={(v: string) => v.slice(5)}
        />
        <YAxis
          tick={{ fontSize: 11 }}
          domain={[0, 100]}
          ticks={[0, 30, 50, 70, 100]}
          width={40}
        />
        <Tooltip
          labelFormatter={(label: string) => label}
          formatter={(value: number, name: string) => [value.toFixed(2), name]}
        />
        <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="4 4" label={{ value: "70", position: "right", fontSize: 10, fill: "#ef4444" }} />
        <ReferenceLine y={30} stroke="#3b82f6" strokeDasharray="4 4" label={{ value: "30", position: "right", fontSize: 10, fill: "#3b82f6" }} />
        <ReferenceLine y={50} stroke="#9ca3af" strokeDasharray="2 2" />
        {assetIds.length > 1 && <Legend />}
        {assetIds.map((id, i) => (
          <Line
            key={id}
            type="monotone"
            dataKey={id}
            name={id}
            stroke={COLORS[i % COLORS.length]}
            dot={false}
            strokeWidth={1.5}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

/** MACD 서브차트 — MACD 라인 + 시그널 라인 + 히스토그램 (단일 자산) */
function MACDChart({ data }: { data: ChartPoint[] }) {
  if (data.length === 0) {
    return <EmptyState />;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={data}>
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11 }}
          tickFormatter={(v: string) => v.slice(5)}
        />
        <YAxis tick={{ fontSize: 11 }} width={50} />
        <Tooltip
          labelFormatter={(label: string) => label}
          formatter={(value: number, name: string) => [value.toFixed(4), name]}
        />
        <Legend />
        <ReferenceLine y={0} stroke="#9ca3af" strokeDasharray="2 2" />
        <Bar
          dataKey="histogram"
          name="히스토그램"
          fill="#94a3b8"
          opacity={0.5}
        />
        <Line
          type="monotone"
          dataKey="macd"
          name="MACD"
          stroke="#2563eb"
          dot={false}
          strokeWidth={1.5}
        />
        <Line
          type="monotone"
          dataKey="signal"
          name="Signal"
          stroke="#ef4444"
          dot={false}
          strokeWidth={1.5}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

/** 일반 팩터 라인 차트 (SMA, EMA, 변동성 등) */
function GenericFactorChart({ data, assetIds }: { data: ChartPoint[]; assetIds: string[] }) {
  if (data.length === 0) {
    return <EmptyState />;
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11 }}
          tickFormatter={(v: string) => v.slice(5)}
        />
        <YAxis tick={{ fontSize: 11 }} width={60} />
        <Tooltip
          labelFormatter={(label: string) => label}
          formatter={(value: number, name: string) => [value.toFixed(4), name]}
        />
        {assetIds.length > 1 && <Legend />}
        {assetIds.map((id, i) => (
          <Line
            key={id}
            type="monotone"
            dataKey={id}
            name={id}
            stroke={COLORS[i % COLORS.length]}
            dot={false}
            strokeWidth={1.5}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

function EmptyState() {
  return (
    <div className="flex items-center justify-center h-64 text-gray-400">
      데이터가 없습니다
    </div>
  );
}

/** 팩터 이름에 따른 표시명 */
const FACTOR_LABELS: Record<string, string> = {
  rsi_14: "RSI (14)",
  macd: "MACD",
  sma_20: "SMA 20",
  sma_60: "SMA 60",
  sma_120: "SMA 120",
  ema_12: "EMA 12",
  ema_26: "EMA 26",
  vol_20: "변동성 (20일)",
  atr_14: "ATR (14)",
  ret_1d: "수익률 1일",
  ret_5d: "수익률 5일",
  ret_20d: "수익률 20일",
  ret_63d: "수익률 63일",
  roc: "ROC",
  vol_zscore_20: "거래량 Z-Score (20)",
};

function getFactorLabel(name: string): string {
  return FACTOR_LABELS[name] || name;
}

export default function FactorChart({ data, factorName, assetIds }: Props) {
  const chartData = mergeFactorByDate(data, assetIds);

  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-2">
        {getFactorLabel(factorName)}
      </h3>
      {factorName === "rsi_14" ? (
        <RSIChart data={chartData} assetIds={assetIds} />
      ) : (
        <GenericFactorChart data={chartData} assetIds={assetIds} />
      )}
    </div>
  );
}

export { mergeMacdData, MACDChart, getFactorLabel, FACTOR_LABELS };
export type { ChartPoint };
