type Option<T> = { value: T; label: string };

type Props<T extends string | number> = {
  options: Option<T>[];
  value: T;
  onChange: (v: T) => void;
  ariaLabel: string;
};

export default function PillGroup<T extends string | number>({
  options,
  value,
  onChange,
  ariaLabel,
}: Props<T>) {
  return (
    <div role="radiogroup" aria-label={ariaLabel} className="silver-pill-group">
      {options.map((opt) => (
        <button
          key={String(opt.value)}
          role="radio"
          aria-checked={value === opt.value}
          className={`silver-pill${value === opt.value ? " silver-pill--active" : ""}`}
          onClick={() => onChange(opt.value)}
          type="button"
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
