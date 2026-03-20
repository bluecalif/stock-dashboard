import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { useProfileStore } from "../../store/profileStore";

/** 페이지별 beginner 가이드 메시지 */
const PAGE_GUIDES: Record<string, { title: string; description: string }> = {
  home: {
    title: "대시보드",
    description:
      "7개 자산의 전체 현황을 한눈에 볼 수 있어요. 각 카드를 클릭하면 상세 페이지로 이동합니다.",
  },
  prices: {
    title: "가격 분석",
    description:
      "자산별 가격 추이와 수익률을 확인할 수 있어요. 기간을 조절해서 단기/장기 흐름을 비교해보세요.",
  },
  correlation: {
    title: "상관관계 분석",
    description:
      "자산 간 가격 움직임의 유사도를 보여줘요. 분산투자에 도움이 되는 조합을 찾아보세요.",
  },
  indicators: {
    title: "지표 & 신호",
    description:
      "RSI, MACD 등 기술적 지표와 매수/매도 신호를 확인할 수 있어요. 투자 타이밍 판단에 활용하세요.",
  },
  strategy: {
    title: "전략 백테스트",
    description:
      "과거 데이터로 투자 전략의 성과를 검증할 수 있어요. 수익률과 위험도를 비교해보세요.",
  },
};

const PATH_TO_PAGE_ID: Record<string, string> = {
  "/": "home",
  "/prices": "prices",
  "/correlation": "correlation",
  "/indicators": "indicators",
  "/strategy": "strategy",
};

const STORAGE_KEY = "page_guide_dismissed";

function getDismissed(): Set<string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? new Set(JSON.parse(raw)) : new Set();
  } catch {
    return new Set();
  }
}

function setDismissed(pageId: string) {
  const dismissed = getDismissed();
  dismissed.add(pageId);
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...dismissed]));
}

export default function PageGuide() {
  const { pathname } = useLocation();
  const profile = useProfileStore((s) => s.profile);
  const [visible, setVisible] = useState(false);
  const [currentGuide, setCurrentGuide] = useState<{
    title: string;
    description: string;
  } | null>(null);

  useEffect(() => {
    if (!profile || profile.experience_level !== "beginner") {
      setVisible(false);
      return;
    }

    const pageId = PATH_TO_PAGE_ID[pathname];
    if (!pageId) {
      setVisible(false);
      return;
    }

    const guide = PAGE_GUIDES[pageId];
    if (!guide || getDismissed().has(pageId)) {
      setVisible(false);
      return;
    }

    setCurrentGuide(guide);
    setVisible(true);
  }, [pathname, profile]);

  if (!visible || !currentGuide) return null;

  const handleDismiss = () => {
    const pageId = PATH_TO_PAGE_ID[pathname];
    if (pageId) setDismissed(pageId);
    setVisible(false);
  };

  return (
    <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 w-full max-w-md px-4 animate-slide-down">
      <div className="bg-blue-50 border border-blue-200 rounded-xl shadow-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-2xl flex-shrink-0">📖</span>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-blue-900 text-sm">
              {currentGuide.title} 페이지 안내
            </h3>
            <p className="text-blue-700 text-sm mt-1 leading-relaxed">
              {currentGuide.description}
            </p>
          </div>
          <button
            onClick={handleDismiss}
            className="flex-shrink-0 text-blue-400 hover:text-blue-600 transition-colors p-1"
            aria-label="닫기"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        <button
          onClick={handleDismiss}
          className="mt-3 w-full text-center text-xs text-blue-500 hover:text-blue-700 transition-colors"
        >
          확인했어요
        </button>
      </div>
    </div>
  );
}
