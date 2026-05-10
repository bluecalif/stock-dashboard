export type TabId = "A" | "B" | "C";

const TABS: { id: TabId; label: string }[] = [
  { id: "A", label: "단일 자산" },
  { id: "B", label: "자산 vs 전략" },
  { id: "C", label: "자산 vs 포트폴리오" },
];

type Props = {
  active: TabId;
  onChange: (id: TabId) => void;
};

export default function TabNav({ active, onChange }: Props) {
  return (
    <div className="silver-pill-group" role="tablist" aria-label="비교 탭">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={active === tab.id}
          className={`silver-pill${active === tab.id ? " silver-pill--active" : ""}`}
          onClick={() => onChange(tab.id)}
          type="button"
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
