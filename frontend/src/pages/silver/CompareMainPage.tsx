import { useState } from "react";
import TabNav, { type TabId } from "./components/TabNav";
import CommonInputPanel from "./components/CommonInputPanel";
import TabA_SingleAsset from "./TabA_SingleAsset";
import TabB_AssetVsStrategy from "./TabB_AssetVsStrategy";
import TabC_AssetVsPortfolio from "./TabC_AssetVsPortfolio";

export default function CompareMainPage() {
  const [activeTab, setActiveTab] = useState<TabId>("A");
  const [periodYears, setPeriodYears] = useState<3 | 5 | 10>(10);
  const [monthlyAmount, setMonthlyAmount] = useState<number>(1_000_000);

  return (
    <div className="silver-section">
      {/* 상단 컨트롤 바 */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 16,
        }}
      >
        <TabNav active={activeTab} onChange={setActiveTab} />
        <CommonInputPanel
          periodYears={periodYears}
          onPeriodChange={setPeriodYears}
          monthlyAmount={monthlyAmount}
          onAmountChange={setMonthlyAmount}
        />
      </div>

      {/* 탭 콘텐츠 */}
      {activeTab === "A" && (
        <TabA_SingleAsset periodYears={periodYears} monthlyAmount={monthlyAmount} />
      )}
      {activeTab === "B" && (
        <TabB_AssetVsStrategy periodYears={periodYears} monthlyAmount={monthlyAmount} />
      )}
      {activeTab === "C" && (
        <TabC_AssetVsPortfolio periodYears={periodYears} monthlyAmount={monthlyAmount} />
      )}
    </div>
  );
}
