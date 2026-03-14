import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

interface Props {
  normedA: number[];
  normedB: number[];
  dates: string[];
  nameA: string;
  nameB: string;
}

interface ReturnPoint {
  x: number;
  y: number;
  date: string;
}

function calcReturns(prices: number[]): number[] {
  const ret: number[] = [];
  for (let i = 1; i < prices.length; i++) {
    ret.push(((prices[i] - prices[i - 1]) / prices[i - 1]) * 100);
  }
  return ret;
}

export default function ReturnScatterChart({
  normedA,
  normedB,
  dates,
  nameA,
  nameB,
}: Props) {
  const retA = calcReturns(normedA);
  const retB = calcReturns(normedB);

  const data: ReturnPoint[] = retA.map((_, i) => ({
    x: retA[i],
    y: retB[i],
    date: dates[i + 1],
  }));

  if (data.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={200}>
      <ScatterChart margin={{ top: 5, right: 20, bottom: 20, left: 10 }}>
        <XAxis
          type="number"
          dataKey="x"
          tick={{ fontSize: 10 }}
          label={{
            value: `${nameA} (%)\u00A0`,
            position: "insideBottom",
            offset: -12,
            fontSize: 10,
          }}
        />
        <YAxis
          type="number"
          dataKey="y"
          tick={{ fontSize: 10 }}
          label={{
            value: `${nameB} (%)`,
            angle: -90,
            position: "insideLeft",
            fontSize: 10,
          }}
        />
        <ZAxis range={[24, 24]} />
        <ReferenceLine x={0} stroke="#d1d5db" strokeDasharray="3 3" />
        <ReferenceLine y={0} stroke="#d1d5db" strokeDasharray="3 3" />
        <Tooltip
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const pt = payload[0].payload as ReturnPoint;
            return (
              <div className="bg-white border border-gray-200 rounded shadow-sm px-3 py-2 text-xs">
                <div className="font-semibold text-gray-800">{pt.date}</div>
                <div style={{ color: "#3b82f6" }}>
                  {nameA}: <span className="font-mono">{pt.x.toFixed(2)}%</span>
                </div>
                <div style={{ color: "#f97316" }}>
                  {nameB}: <span className="font-mono">{pt.y.toFixed(2)}%</span>
                </div>
              </div>
            );
          }}
        />
        <Scatter data={data} fill="#6366f1" fillOpacity={0.6} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
