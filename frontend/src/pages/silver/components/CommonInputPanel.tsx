import PillGroup from "./PillGroup";

const PERIOD_OPTIONS = [
  { value: 3 as const, label: "3년" },
  { value: 5 as const, label: "5년" },
  { value: 10 as const, label: "10년" },
];

const AMOUNT_OPTIONS = [
  { value: 300_000, label: "30만" },
  { value: 500_000, label: "50만" },
  { value: 1_000_000, label: "100만" },
  { value: 2_000_000, label: "200만" },
  { value: 3_000_000, label: "300만" },
];

type Props = {
  periodYears: 3 | 5 | 10;
  onPeriodChange: (v: 3 | 5 | 10) => void;
  monthlyAmount: number;
  onAmountChange: (v: number) => void;
};

export default function CommonInputPanel({
  periodYears,
  onPeriodChange,
  monthlyAmount,
  onAmountChange,
}: Props) {
  return (
    <div className="silver-input-panel">
      <div className="silver-input-panel__row">
        <span className="silver-input-panel__label">기간</span>
        <PillGroup
          options={PERIOD_OPTIONS}
          value={periodYears}
          onChange={onPeriodChange}
          ariaLabel="투자 기간 선택"
        />
      </div>
      <div className="silver-input-panel__row">
        <span className="silver-input-panel__label">월 적립금</span>
        <PillGroup
          options={AMOUNT_OPTIONS}
          value={monthlyAmount}
          onChange={onAmountChange}
          ariaLabel="월 적립금 선택"
        />
      </div>
    </div>
  );
}
