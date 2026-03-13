import { create } from "zustand";
import type { UIAction } from "../types/chat";

interface ChartActionState {
  /** 처리 대기 중인 UI 액션 큐 */
  queue: UIAction[];

  /** 액션 추가 */
  push: (action: UIAction) => void;

  /** 큐에서 첫 번째 액션을 꺼내서 반환 */
  shift: () => UIAction | undefined;

  /** 큐 전체 비우기 */
  clear: () => void;

  /** 현재 하이라이트된 페어 */
  highlightedPair: { asset_a: string; asset_b: string } | null;
  setHighlightedPair: (pair: { asset_a: string; asset_b: string } | null) => void;

  /** 현재 필터 상태 */
  filters: Record<string, string | string[]>;
  setFilter: (key: string, value: string | string[]) => void;
  clearFilters: () => void;
}

export const useChartActionStore = create<ChartActionState>((set, get) => ({
  queue: [],

  push: (action) =>
    set((s) => ({ queue: [...s.queue, action] })),

  shift: () => {
    const q = get().queue;
    if (q.length === 0) return undefined;
    const [first, ...rest] = q;
    set({ queue: rest });
    return first;
  },

  clear: () => set({ queue: [] }),

  highlightedPair: null,
  setHighlightedPair: (pair) => set({ highlightedPair: pair }),

  filters: {},
  setFilter: (key, value) =>
    set((s) => ({ filters: { ...s.filters, [key]: value } })),
  clearFilters: () => set({ filters: {} }),
}));
