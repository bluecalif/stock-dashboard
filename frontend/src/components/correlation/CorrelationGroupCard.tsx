import { useState } from "react";
import type { CorrelationGroup } from "../../types/api";

interface Props {
  groups: CorrelationGroup[];
  onGroupClick?: (group: CorrelationGroup) => void;
  onPairSelect?: (assetA: string, assetB: string) => void;
  nameMap?: Record<string, string>;
}

const GROUP_COLORS = [
  "bg-blue-50 border-blue-200",
  "bg-green-50 border-green-200",
  "bg-purple-50 border-purple-200",
  "bg-orange-50 border-orange-200",
  "bg-pink-50 border-pink-200",
];

function strengthLabel(avg: number): string {
  if (avg >= 0.9) return "매우 강한 상관";
  if (avg >= 0.7) return "강한 상관";
  if (avg >= 0.5) return "보통 상관";
  return "약한 상관";
}

/** Generate all unique pairs from asset IDs */
function makePairs(ids: string[]): [string, string][] {
  const pairs: [string, string][] = [];
  for (let i = 0; i < ids.length; i++) {
    for (let j = i + 1; j < ids.length; j++) {
      pairs.push([ids[i], ids[j]]);
    }
  }
  return pairs;
}

export default function CorrelationGroupCard({
  groups,
  onGroupClick,
  onPairSelect,
  nameMap = {},
}: Props) {
  const [expandedGroup, setExpandedGroup] = useState<number | null>(null);
  const dn = (id: string) => nameMap[id] || id;

  if (groups.length === 0) {
    return (
      <p className="text-gray-400 text-sm text-center py-4">
        현재 임계값에서 발견된 그룹이 없습니다.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {groups.map((g, idx) => {
        const pairs = makePairs(g.asset_ids);
        const showPairSelect = g.asset_ids.length >= 3;

        return (
          <div
            key={g.group_id}
            className={`rounded-lg border p-4 text-left transition-shadow hover:shadow-md ${
              GROUP_COLORS[idx % GROUP_COLORS.length]
            }`}
          >
            <button
              className="w-full text-left"
              onClick={() => {
                onGroupClick?.(g);
                if (showPairSelect) {
                  setExpandedGroup(expandedGroup === g.group_id ? null : g.group_id);
                } else if (g.asset_ids.length >= 2 && onPairSelect) {
                  onPairSelect(g.asset_ids[0], g.asset_ids[1]);
                }
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-gray-500">
                  그룹 {g.group_id + 1}
                </span>
                <span className="text-xs text-gray-400">
                  {strengthLabel(g.avg_correlation)}
                </span>
              </div>
              <div className="flex flex-wrap gap-1 mb-2">
                {g.asset_ids.map((id) => (
                  <span
                    key={id}
                    className="inline-block bg-white rounded px-2 py-0.5 text-xs font-medium text-gray-700 border border-gray-200"
                    title={id}
                  >
                    {dn(id)}
                  </span>
                ))}
              </div>
              <div className="text-sm font-mono font-semibold text-gray-800">
                avg {g.avg_correlation.toFixed(2)}
              </div>
            </button>

            {/* 3종목 이상 그룹: 페어 선택 */}
            {showPairSelect && expandedGroup === g.group_id && (
              <div className="mt-2 pt-2 border-t border-gray-200 flex flex-wrap gap-1">
                {pairs.map(([a, b]) => (
                  <button
                    key={`${a}-${b}`}
                    onClick={() => onPairSelect?.(a, b)}
                    className="text-xs px-2 py-1 rounded bg-white border border-gray-300 hover:border-blue-400 hover:bg-blue-50 transition-colors"
                  >
                    {dn(a)} ↔ {dn(b)}
                  </button>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
