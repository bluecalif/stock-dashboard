import { useState, useEffect } from "react";

export type AssetDef = {
  code: string;
  label: string;
  category: string;
};

type Props = {
  open: boolean;
  onClose: () => void;
  universe: AssetDef[];
  selected: string[];
  onChange: (selected: string[]) => void;
  maxSelect: number;
  title: string;
};

export default function AssetPickerDrawer({
  open,
  onClose,
  universe,
  selected,
  onChange,
  maxSelect,
  title,
}: Props) {
  const [draft, setDraft] = useState<string[]>(selected);

  useEffect(() => {
    if (open) setDraft(selected);
  }, [open, selected]);

  function toggle(code: string) {
    setDraft((prev) => {
      if (prev.includes(code)) {
        return prev.filter((c) => c !== code);
      }
      if (prev.length >= maxSelect) return prev;
      return [...prev, code];
    });
  }

  function handleConfirm() {
    if (draft.length === 0) return;
    onChange(draft);
    onClose();
  }

  const categories = Array.from(new Set(universe.map((a) => a.category)));

  return (
    <>
      <div
        className={`silver-drawer-backdrop${open ? " silver-drawer-backdrop--open" : ""}`}
        onClick={onClose}
      />
      <div className={`silver-drawer${open ? " silver-drawer--open" : ""}`} role="dialog" aria-modal="true">
        <div className="silver-drawer__header">
          <span className="silver-drawer__title">{title}</span>
          <button className="silver-drawer__close" onClick={onClose} aria-label="닫기">
            ×
          </button>
        </div>

        <div className="silver-drawer__body">
          {maxSelect > 1 && (
            <p style={{ fontSize: 12, color: "var(--text-tertiary)", marginBottom: 12 }}>
              최대 {maxSelect}종 선택 · 현재 {draft.length}종 선택됨
            </p>
          )}

          {categories.map((cat) => (
            <div key={cat}>
              <div className="silver-drawer__category">{cat}</div>
              {universe
                .filter((a) => a.category === cat)
                .map((asset) => {
                  const checked = draft.includes(asset.code);
                  const disabled = !checked && draft.length >= maxSelect;
                  return (
                    <label
                      key={asset.code}
                      className="silver-drawer__item"
                      style={{ opacity: disabled ? 0.4 : 1 }}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        disabled={disabled}
                        onChange={() => toggle(asset.code)}
                      />
                      <span className="silver-drawer__item-label">{asset.label}</span>
                    </label>
                  );
                })}
            </div>
          ))}
        </div>

        <div className="silver-drawer__footer">
          <button className="silver-btn-ghost" onClick={onClose}>
            취소
          </button>
          <button
            className="silver-btn-primary"
            onClick={handleConfirm}
            disabled={draft.length === 0}
          >
            적용 ({draft.length}종)
          </button>
        </div>
      </div>
    </>
  );
}
