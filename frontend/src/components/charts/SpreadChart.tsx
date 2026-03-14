import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
} from "recharts";
import type { SpreadResponse } from "../../types/api";

interface Props {
  spread: SpreadResponse;
}

interface ChartPoint {
  date: string;
  z_score: number;
  spread: number;
}

function zScoreColor(z: number): string {
  if (Math.abs(z) >= 2.0) return "#ef4444"; // red — extreme
  if (Math.abs(z) >= 1.0) return "#f59e0b"; // amber — warning
  return "#22c55e"; // green — normal
}

export default function SpreadChart({ spread }: Props) {
  const dn = (id: string) => spread.asset_names?.[id] || id;
  const data: ChartPoint[] = spread.dates.map((d, i) => ({
    date: d,
    z_score: spread.z_scores[i],
    spread: spread.spread_values[i],
  }));

  if (data.length === 0) {
    return (
      <p className="text-gray-400 text-sm text-center py-8">
        스프레드 데이터가 없습니다.
      </p>
    );
  }

  const currentZ = spread.current_z_score;
  const statusLabel =
    Math.abs(currentZ) >= 2.0
      ? "극단적 이탈"
      : Math.abs(currentZ) >= 1.0
        ? "주의 구간"
        : "정상 범위";
  const statusColor = zScoreColor(currentZ);

  return (
    <div>
      {/* Status badge */}
      <div className="flex items-center gap-3 mb-3">
        <span className="text-sm font-medium text-gray-700">
          {dn(spread.asset_a)} ↔ {dn(spread.asset_b)}
        </span>
        <span
          className="text-xs font-semibold px-2 py-0.5 rounded"
          style={{ backgroundColor: statusColor + "20", color: statusColor }}
        >
          Z={currentZ.toFixed(2)} · {statusLabel}
        </span>
      </div>

      {/* Z-score chart */}
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
          {/* ±2σ extreme band */}
          <ReferenceArea y1={2} y2={4} fill="#fecaca" fillOpacity={0.3} />
          <ReferenceArea y1={-4} y2={-2} fill="#fecaca" fillOpacity={0.3} />
          {/* ±1σ warning band */}
          <ReferenceArea y1={1} y2={2} fill="#fef3c7" fillOpacity={0.3} />
          <ReferenceArea y1={-2} y2={-1} fill="#fef3c7" fillOpacity={0.3} />

          <XAxis
            dataKey="date"
            tick={{ fontSize: 10 }}
            tickFormatter={(v: string) => v.slice(5)}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 11 }}
            label={{ value: "Z-Score", angle: -90, position: "insideLeft", fontSize: 11 }}
          />

          <ReferenceLine y={0} stroke="#9ca3af" strokeDasharray="3 3" />
          <ReferenceLine y={2} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.6} />
          <ReferenceLine y={-2} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.6} />
          <ReferenceLine y={1} stroke="#f59e0b" strokeDasharray="3 3" strokeOpacity={0.4} />
          <ReferenceLine y={-1} stroke="#f59e0b" strokeDasharray="3 3" strokeOpacity={0.4} />

          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const pt = payload[0].payload as ChartPoint;
              return (
                <div className="bg-white border border-gray-200 rounded shadow-sm px-3 py-2 text-xs">
                  <div className="font-semibold text-gray-800">{pt.date}</div>
                  <div className="text-gray-600">
                    Z-Score: <span className="font-mono">{pt.z_score.toFixed(3)}</span>
                  </div>
                  <div className="text-gray-500">
                    Spread: <span className="font-mono">{pt.spread.toFixed(4)}</span>
                  </div>
                </div>
              );
            }}
          />

          <Line
            type="monotone"
            dataKey="z_score"
            stroke="#3b82f6"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 4, fill: "#3b82f6" }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Convergence events */}
      {spread.convergence_events.length > 0 && (
        <div className="mt-3">
          <h4 className="text-xs font-semibold text-gray-600 mb-1">
            최근 수렴/발산 이벤트
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {spread.convergence_events.slice(-6).map((e, i) => (
              <span
                key={i}
                className={`text-xs px-2 py-0.5 rounded ${
                  e.direction === "convergence"
                    ? "bg-green-50 text-green-700"
                    : "bg-red-50 text-red-700"
                }`}
              >
                {e.date.slice(5)} {e.direction === "convergence" ? "수렴" : "발산"}{" "}
                <span className="font-mono">z={e.z_score.toFixed(2)}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
