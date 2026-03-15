import { getFactorLabel } from "../charts/FactorChart";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type NormalizeMode = "raw" | "normalized" | "percent";

interface IndicatorSetting {
  factorName: string;
  visible: boolean;
}

interface Props {
  /** 선택된 팩터 목록 (로드된 팩터) */
  availableFactors: string[];
  /** 오버레이에 표시할 팩터 설정 */
  settings: IndicatorSetting[];
  onSettingsChange: (settings: IndicatorSetting[]) => void;
  /** 정규화 모드 */
  normalizeMode: NormalizeMode;
  onNormalizeModeChange: (mode: NormalizeMode) => void;
}

const NORMALIZE_OPTIONS: { id: NormalizeMode; label: string; desc: string }[] =
  [
    { id: "raw", label: "원본", desc: "원래 단위 그대로 표시" },
    { id: "normalized", label: "정규화", desc: "0~100 범위로 변환" },
    {
      id: "percent",
      label: "% 변화",
      desc: "시작점 대비 변화율로 비교",
    },
  ];

// Overlay에서 제외할 팩터 (별도 차트가 더 적합)
const OVERLAY_EXCLUDED = new Set(["macd"]);

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function IndicatorSettingsPanel({
  availableFactors,
  settings,
  onSettingsChange,
  normalizeMode,
  onNormalizeModeChange,
}: Props) {
  const overlayFactors = availableFactors.filter(
    (f) => !OVERLAY_EXCLUDED.has(f),
  );

  const toggleFactor = (factorName: string) => {
    const updated = settings.map((s) =>
      s.factorName === factorName ? { ...s, visible: !s.visible } : s,
    );
    // If factor is new (not in settings yet), add it as visible
    if (!settings.find((s) => s.factorName === factorName)) {
      updated.push({ factorName, visible: true });
    }
    onSettingsChange(updated);
  };

  const showAll = () => {
    onSettingsChange(
      overlayFactors.map((f) => ({ factorName: f, visible: true })),
    );
  };

  const hideAll = () => {
    onSettingsChange(
      overlayFactors.map((f) => ({ factorName: f, visible: false })),
    );
  };

  const isVisible = (factorName: string) =>
    settings.find((s) => s.factorName === factorName)?.visible ?? true;

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
          오버레이 설정
        </h4>
        <div className="flex gap-2">
          <button
            onClick={showAll}
            className="text-xs text-indigo-600 hover:text-indigo-800"
          >
            전체 표시
          </button>
          <span className="text-gray-300">|</span>
          <button
            onClick={hideAll}
            className="text-xs text-indigo-600 hover:text-indigo-800"
          >
            전체 숨김
          </button>
        </div>
      </div>

      {/* Indicator toggles */}
      <div>
        <label className="block text-xs text-gray-500 mb-1.5">
          지표 표시/숨기기
        </label>
        <div className="flex flex-wrap gap-2">
          {overlayFactors.map((f) => {
            const visible = isVisible(f);
            return (
              <button
                key={f}
                onClick={() => toggleFactor(f)}
                className={`px-2.5 py-1 rounded text-xs font-medium border transition-colors ${
                  visible
                    ? "bg-white text-gray-800 border-gray-300 shadow-sm"
                    : "bg-gray-100 text-gray-400 border-gray-200 line-through"
                }`}
              >
                {getFactorLabel(f)}
              </button>
            );
          })}
          {overlayFactors.length === 0 && (
            <span className="text-xs text-gray-400">
              팩터를 선택하면 여기에 표시됩니다
            </span>
          )}
        </div>
      </div>

      {/* Normalize mode */}
      <div>
        <label className="block text-xs text-gray-500 mb-1.5">
          표시 모드
        </label>
        <div className="flex gap-2">
          {NORMALIZE_OPTIONS.map((opt) => (
            <button
              key={opt.id}
              onClick={() => onNormalizeModeChange(opt.id)}
              className={`px-3 py-1.5 rounded text-xs font-medium border transition-colors ${
                normalizeMode === opt.id
                  ? "bg-indigo-600 text-white border-indigo-600"
                  : "bg-white text-gray-700 border-gray-300 hover:border-indigo-400"
              }`}
              title={opt.desc}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-400 mt-1">
          {NORMALIZE_OPTIONS.find((o) => o.id === normalizeMode)?.desc}
        </p>
      </div>
    </div>
  );
}

export type { IndicatorSetting };
