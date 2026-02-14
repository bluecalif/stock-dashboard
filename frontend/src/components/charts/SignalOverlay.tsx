import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Scatter,
  Cell,
} from "recharts";
import type { PriceDailyResponse, SignalDailyResponse } from "../../types/api";

interface ChartPoint {
  date: string;
  close: number;
  signal?: number; // 1=매수, -1=청산
  action?: string;
  score?: number | null;
}

interface Props {
  prices: PriceDailyResponse[];
  signals: SignalDailyResponse[];
  assetId: string;
  strategyId: string;
}

function formatPrice(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return value.toLocaleString();
  return value.toFixed(2);
}

/** 삼각형 마커: 매수(▲ 초록), 청산(▼ 빨강) */
function SignalMarker(props: {
  cx?: number;
  cy?: number;
  payload?: ChartPoint;
}) {
  const { cx, cy, payload } = props;
  if (cx == null || cy == null || !payload?.signal) return null;

  const isBuy = payload.signal === 1;
  const color = isBuy ? "#16a34a" : "#dc2626";
  const size = 8;

  // 삼각형 path: ▲(매수) 위쪽, ▼(청산) 아래쪽
  const path = isBuy
    ? `M${cx},${cy - size} L${cx - size},${cy + size} L${cx + size},${cy + size} Z`
    : `M${cx},${cy + size} L${cx - size},${cy - size} L${cx + size},${cy - size} Z`;

  return <path d={path} fill={color} stroke={color} strokeWidth={1} />;
}

export default function SignalOverlay({
  prices,
  signals,
  assetId,
  strategyId,
}: Props) {
  if (prices.length === 0) {
    return (
      <div className="flex items-center justify-center h-80 text-gray-400">
        데이터가 없습니다
      </div>
    );
  }

  // 시그널을 date 기반 Map으로 변환
  const signalMap = new Map<string, SignalDailyResponse>();
  for (const s of signals) {
    if (s.asset_id === assetId && s.strategy_id === strategyId) {
      signalMap.set(s.date, s);
    }
  }

  // 가격 + 시그널 병합
  const data: ChartPoint[] = prices
    .filter((p) => p.asset_id === assetId)
    .map((p) => {
      const sig = signalMap.get(p.date);
      return {
        date: p.date,
        close: p.close,
        signal: sig && sig.signal !== 0 ? sig.signal : undefined,
        action: sig?.action ?? undefined,
        score: sig?.score,
      };
    });

  // 시그널 포인트만 필터 (Scatter용)
  const signalPoints = data.filter((d) => d.signal !== undefined);

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ComposedChart data={data}>
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11 }}
          tickFormatter={(v: string) => v.slice(5)}
        />
        <YAxis
          tick={{ fontSize: 11 }}
          tickFormatter={formatPrice}
          width={70}
          domain={["auto", "auto"]}
        />
        <Tooltip
          labelFormatter={(label: string) => label}
          formatter={(value: number, name: string) => {
            if (name === "close") return [formatPrice(value), "종가"];
            return [value, name];
          }}
          content={({ active, payload, label }) => {
            if (!active || !payload?.length) return null;
            const point = payload[0]?.payload as ChartPoint | undefined;
            return (
              <div className="bg-white border border-gray-200 rounded shadow-sm px-3 py-2 text-xs">
                <p className="font-medium text-gray-700">{label}</p>
                <p className="text-gray-600">
                  종가: {point ? formatPrice(point.close) : "—"}
                </p>
                {point?.signal && (
                  <p
                    className={
                      point.signal === 1 ? "text-green-600" : "text-red-600"
                    }
                  >
                    {point.signal === 1 ? "▲ 매수" : "▼ 청산"}
                    {point.action ? ` (${point.action})` : ""}
                    {point.score != null
                      ? ` score: ${point.score.toFixed(2)}`
                      : ""}
                  </p>
                )}
              </div>
            );
          }}
        />
        <Line
          type="monotone"
          dataKey="close"
          stroke="#2563eb"
          dot={false}
          strokeWidth={1.5}
          name="close"
        />
        <Scatter
          data={signalPoints}
          dataKey="close"
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          shape={<SignalMarker /> as any}
          legendType="none"
        >
          {signalPoints.map((pt, i) => (
            <Cell
              key={`sig-${i}`}
              fill={pt.signal === 1 ? "#16a34a" : "#dc2626"}
            />
          ))}
        </Scatter>
      </ComposedChart>
    </ResponsiveContainer>
  );
}
