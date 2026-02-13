import { useState } from "react";

interface Props {
  assetIds: string[];
  matrix: number[][];
}

/** -1(파랑) ~ 0(흰) ~ +1(빨강) 색상 보간 */
function correlationColor(value: number): string {
  const clamped = Math.max(-1, Math.min(1, value));
  if (clamped >= 0) {
    // 0 → white, +1 → red
    const r = 255;
    const g = Math.round(255 * (1 - clamped));
    const b = Math.round(255 * (1 - clamped));
    return `rgb(${r},${g},${b})`;
  }
  // -1 → blue, 0 → white
  const abs = Math.abs(clamped);
  const r = Math.round(255 * (1 - abs));
  const g = Math.round(255 * (1 - abs));
  const b = 255;
  return `rgb(${r},${g},${b})`;
}

/** 값에 따른 텍스트 색상 (진한 배경에는 흰 글씨) */
function textColor(value: number): string {
  return Math.abs(value) > 0.6 ? "#fff" : "#1f2937";
}

export default function CorrelationHeatmap({ assetIds, matrix }: Props) {
  const [hovered, setHovered] = useState<{ row: number; col: number } | null>(
    null,
  );
  const n = assetIds.length;

  if (n === 0) {
    return (
      <p className="text-gray-400 text-sm text-center py-8">
        데이터가 없습니다.
      </p>
    );
  }

  const cellSize = n <= 5 ? 72 : n <= 8 ? 60 : 48;
  const labelWidth = 80;

  return (
    <div className="overflow-x-auto">
      {/* 상단 라벨 */}
      <div className="flex" style={{ paddingLeft: labelWidth }}>
        {assetIds.map((id) => (
          <div
            key={id}
            className="text-xs font-medium text-gray-600 text-center truncate"
            style={{ width: cellSize, flexShrink: 0 }}
          >
            {id}
          </div>
        ))}
      </div>

      {/* 행별 렌더링 */}
      {matrix.map((row, i) => (
        <div key={assetIds[i]} className="flex items-center">
          {/* 좌측 라벨 */}
          <div
            className="text-xs font-medium text-gray-600 text-right pr-2 truncate"
            style={{ width: labelWidth, flexShrink: 0 }}
          >
            {assetIds[i]}
          </div>

          {/* 셀 */}
          {row.map((value, j) => {
            const isHovered =
              hovered !== null && hovered.row === i && hovered.col === j;
            return (
              <div
                key={`${i}-${j}`}
                className="relative flex items-center justify-center border border-white transition-transform"
                style={{
                  width: cellSize,
                  height: cellSize,
                  flexShrink: 0,
                  backgroundColor: correlationColor(value),
                  color: textColor(value),
                  transform: isHovered ? "scale(1.08)" : undefined,
                  zIndex: isHovered ? 10 : undefined,
                }}
                onMouseEnter={() => setHovered({ row: i, col: j })}
                onMouseLeave={() => setHovered(null)}
              >
                <span className="text-xs font-mono font-semibold">
                  {value.toFixed(2)}
                </span>

                {/* 호버 툴팁 */}
                {isHovered && (
                  <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-20 pointer-events-none">
                    {assetIds[i]} × {assetIds[j]}: {value.toFixed(4)}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ))}

      {/* 범례 */}
      <div className="flex items-center gap-2 mt-4 ml-auto w-fit">
        <span className="text-xs text-gray-500">-1</span>
        <div
          className="h-3 rounded"
          style={{
            width: 120,
            background:
              "linear-gradient(to right, rgb(0,0,255), rgb(255,255,255), rgb(255,0,0))",
          }}
        />
        <span className="text-xs text-gray-500">+1</span>
      </div>
    </div>
  );
}
