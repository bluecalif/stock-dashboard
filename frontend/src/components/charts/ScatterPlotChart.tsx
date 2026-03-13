import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { AssetPair } from "../../types/api";

interface Props {
  pairs: AssetPair[];
  highlightPair?: { asset_a: string; asset_b: string } | null;
  onPairClick?: (pair: AssetPair) => void;
}

interface ScatterPoint {
  x: number;
  y: number;
  label: string;
  pair: AssetPair;
}

function pairColor(corr: number, highlighted: boolean): string {
  if (highlighted) return "#f59e0b";
  if (corr >= 0.7) return "#ef4444";
  if (corr >= 0.3) return "#f97316";
  if (corr >= -0.3) return "#6b7280";
  if (corr >= -0.7) return "#3b82f6";
  return "#1d4ed8";
}

export default function ScatterPlotChart({
  pairs,
  highlightPair,
  onPairClick,
}: Props) {
  if (pairs.length === 0) {
    return (
      <p className="text-gray-400 text-sm text-center py-8">
        데이터가 없습니다.
      </p>
    );
  }

  const data: ScatterPoint[] = pairs.map((p, idx) => ({
    x: idx + 1,
    y: p.correlation,
    label: `${p.asset_a}↔${p.asset_b}`,
    pair: p,
  }));

  const isHighlighted = (p: AssetPair) =>
    highlightPair !== null &&
    highlightPair !== undefined &&
    ((p.asset_a === highlightPair.asset_a && p.asset_b === highlightPair.asset_b) ||
      (p.asset_a === highlightPair.asset_b && p.asset_b === highlightPair.asset_a));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
        <XAxis
          type="number"
          dataKey="x"
          name="순위"
          tick={{ fontSize: 11 }}
          label={{ value: "순위", position: "insideBottom", offset: -10, fontSize: 11 }}
        />
        <YAxis
          type="number"
          dataKey="y"
          name="상관계수"
          domain={[-1, 1]}
          tick={{ fontSize: 11 }}
          label={{ value: "상관계수", angle: -90, position: "insideLeft", fontSize: 11 }}
        />
        <ZAxis range={[80, 80]} />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const pt = payload[0].payload as ScatterPoint;
            return (
              <div className="bg-white border border-gray-200 rounded shadow-sm px-3 py-2 text-xs">
                <div className="font-semibold text-gray-800">{pt.label}</div>
                <div className="text-gray-500">
                  상관계수: <span className="font-mono">{pt.y.toFixed(4)}</span>
                </div>
              </div>
            );
          }}
        />
        <Scatter
          data={data}
          onClick={(entry) => {
            if (entry && onPairClick) {
              onPairClick((entry as unknown as ScatterPoint).pair);
            }
          }}
        >
          {data.map((pt, idx) => (
            <Cell
              key={idx}
              fill={pairColor(pt.y, isHighlighted(pt.pair))}
              stroke={isHighlighted(pt.pair) ? "#d97706" : "none"}
              strokeWidth={isHighlighted(pt.pair) ? 2 : 0}
              cursor="pointer"
            />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
}
