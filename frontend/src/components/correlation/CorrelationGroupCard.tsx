import type { CorrelationGroup } from "../../types/api";

interface Props {
  groups: CorrelationGroup[];
  onGroupClick?: (group: CorrelationGroup) => void;
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

export default function CorrelationGroupCard({ groups, onGroupClick, nameMap = {} }: Props) {
  if (groups.length === 0) {
    return (
      <p className="text-gray-400 text-sm text-center py-4">
        현재 임계값에서 발견된 그룹이 없습니다.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {groups.map((g, idx) => (
        <button
          key={g.group_id}
          onClick={() => onGroupClick?.(g)}
          className={`rounded-lg border p-4 text-left transition-shadow hover:shadow-md ${
            GROUP_COLORS[idx % GROUP_COLORS.length]
          }`}
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
                {nameMap[id] || id}
              </span>
            ))}
          </div>
          <div className="text-sm font-mono font-semibold text-gray-800">
            avg {g.avg_correlation.toFixed(2)}
          </div>
        </button>
      ))}
    </div>
  );
}
