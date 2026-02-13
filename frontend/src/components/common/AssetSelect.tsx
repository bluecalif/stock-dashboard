import { useEffect, useState } from "react";
import { fetchAssets } from "../../api/assets";
import type { AssetResponse } from "../../types/api";

interface Props {
  value: string;
  onChange: (assetId: string) => void;
  multiple?: boolean;
  selectedIds?: string[];
  onChangeMultiple?: (ids: string[]) => void;
}

export default function AssetSelect({
  value,
  onChange,
  multiple,
  selectedIds,
  onChangeMultiple,
}: Props) {
  const [assets, setAssets] = useState<AssetResponse[]>([]);

  useEffect(() => {
    fetchAssets(true).then(setAssets).catch(console.error);
  }, []);

  if (multiple && onChangeMultiple) {
    return (
      <div className="flex flex-wrap gap-2">
        {assets.map((a) => {
          const selected = selectedIds?.includes(a.asset_id);
          return (
            <button
              key={a.asset_id}
              onClick={() => {
                const ids = selectedIds || [];
                onChangeMultiple(
                  selected
                    ? ids.filter((id) => id !== a.asset_id)
                    : [...ids, a.asset_id],
                );
              }}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                selected
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
              }`}
            >
              {a.name}
            </button>
          );
        })}
      </div>
    );
  }

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="border border-gray-300 rounded-md px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      <option value="">자산 선택</option>
      {assets.map((a) => (
        <option key={a.asset_id} value={a.asset_id}>
          {a.name} ({a.asset_id})
        </option>
      ))}
    </select>
  );
}
