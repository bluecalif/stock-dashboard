import { useState } from "react";

export type StrategyName = "momentum" | "contrarian" | "risk_aversion";

interface StrategyInfo {
  id: StrategyName;
  label: string;
  indicator: string;
  shortDesc: string;
  longDesc: string;
  color: string;
  icon: string;
}

const STRATEGY_INFO: StrategyInfo[] = [
  {
    id: "momentum",
    label: "모멘텀",
    indicator: "MACD",
    shortDesc: "추세에 올라타는 전략",
    longDesc:
      "MACD 시그널을 따라 추세에 올라타는 전략입니다. MACD 골든크로스 시 매수, 데드크로스 시 매도합니다. 강한 추세 시장에서 효과적이며, 횡보장에서는 잦은 거래로 손실이 발생할 수 있습니다.",
    color: "blue",
    icon: "📈",
  },
  {
    id: "contrarian",
    label: "역추세",
    indicator: "RSI 14",
    shortDesc: "과매도 반등을 노리는 전략",
    longDesc:
      "RSI 과매도 구간(30 이하)에서 반등을 노리는 역추세 전략입니다. 과매도 시 매수, 과매수(70 이상) 시 매도합니다. 변동성이 큰 시장에서 효과적이며, 강한 하락 추세에서는 조기 진입 위험이 있습니다.",
    color: "emerald",
    icon: "🔄",
  },
  {
    id: "risk_aversion",
    label: "위험회피",
    indicator: "ATR + 변동성",
    shortDesc: "변동성 급등 시 시장을 떠나는 전략",
    longDesc:
      "ATR과 변동성 급등 시 시장을 떠나 손실을 줄이는 전략입니다. 평상시에는 시장에 투자하고, 변동성이 급등하면 현금으로 전환합니다. 급락장에서 손실을 제한할 수 있지만, 변동성 이후 빠른 반등을 놓칠 수 있습니다.",
    color: "amber",
    icon: "🛡️",
  },
];

const COLOR_MAP: Record<
  string,
  { bg: string; border: string; ring: string; badge: string; text: string }
> = {
  blue: {
    bg: "bg-blue-50",
    border: "border-blue-200",
    ring: "ring-blue-500",
    badge: "bg-blue-100 text-blue-700",
    text: "text-blue-700",
  },
  emerald: {
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    ring: "ring-emerald-500",
    badge: "bg-emerald-100 text-emerald-700",
    text: "text-emerald-700",
  },
  amber: {
    bg: "bg-amber-50",
    border: "border-amber-200",
    ring: "ring-amber-500",
    badge: "bg-amber-100 text-amber-700",
    text: "text-amber-700",
  },
};

interface Props {
  selected: StrategyName;
  onSelect: (strategy: StrategyName) => void;
}

export default function StrategyDescriptionCard({
  selected,
  onSelect,
}: Props) {
  const [expanded, setExpanded] = useState<StrategyName | null>(null);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {STRATEGY_INFO.map((s) => {
        const isSelected = selected === s.id;
        const isExpanded = expanded === s.id;
        const c = COLOR_MAP[s.color];

        return (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            className={`text-left rounded-lg border-2 p-3 transition-all ${
              isSelected
                ? `${c.bg} ${c.border} ring-2 ${c.ring}`
                : "bg-white border-gray-200 hover:border-gray-300"
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <span className="text-lg">{s.icon}</span>
                <span className="font-semibold text-sm text-gray-900">
                  {s.label}
                </span>
              </div>
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${c.badge}`}
              >
                {s.indicator}
              </span>
            </div>
            <p className="text-xs text-gray-500 mb-1">{s.shortDesc}</p>
            {isExpanded ? (
              <p className="text-xs text-gray-600 mt-2 leading-relaxed">
                {s.longDesc}
              </p>
            ) : (
              <span
                onClick={(e) => {
                  e.stopPropagation();
                  setExpanded(s.id);
                }}
                className={`text-xs cursor-pointer ${c.text} hover:underline`}
              >
                자세히 보기
              </span>
            )}
            {isExpanded && (
              <span
                onClick={(e) => {
                  e.stopPropagation();
                  setExpanded(null);
                }}
                className={`text-xs cursor-pointer ${c.text} hover:underline mt-1 inline-block`}
              >
                접기
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

export { STRATEGY_INFO };
