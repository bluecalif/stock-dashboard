interface Props {
  startDate: string;
  endDate: string;
  onStartChange: (v: string) => void;
  onEndChange: (v: string) => void;
}

const PRESETS = [
  { label: "1M", months: 1 },
  { label: "3M", months: 3 },
  { label: "6M", months: 6 },
  { label: "1Y", months: 12 },
  { label: "3Y", months: 36 },
];

function subtractMonths(months: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() - months);
  return d.toISOString().slice(0, 10);
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function DateRangePicker({
  startDate,
  endDate,
  onStartChange,
  onEndChange,
}: Props) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      {PRESETS.map(({ label, months }) => (
        <button
          key={label}
          onClick={() => {
            onStartChange(subtractMonths(months));
            onEndChange(today());
          }}
          className="px-2.5 py-1 text-xs rounded border border-gray-300 bg-white hover:bg-gray-100 transition-colors"
        >
          {label}
        </button>
      ))}
      <input
        type="date"
        value={startDate}
        onChange={(e) => onStartChange(e.target.value)}
        className="border border-gray-300 rounded px-2 py-1 text-sm"
      />
      <span className="text-gray-400">~</span>
      <input
        type="date"
        value={endDate}
        onChange={(e) => onEndChange(e.target.value)}
        className="border border-gray-300 rounded px-2 py-1 text-sm"
      />
    </div>
  );
}
