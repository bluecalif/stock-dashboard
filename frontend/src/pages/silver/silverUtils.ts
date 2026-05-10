import type { EquityPoint } from "../../types/api";

export function formatKRW(n: number): string {
  if (n >= 100_000_000) return `${(n / 100_000_000).toFixed(1)}억원`;
  if (n >= 10_000) return `${(n / 10_000).toFixed(0)}만원`;
  return `${n.toLocaleString("ko-KR")}원`;
}

export function formatPct(n: number): string {
  const sign = n >= 0 ? "+" : "";
  return `${sign}${(n * 100).toFixed(1)}%`;
}

export type ChartRow = Record<string, number | string>;

export function mergeEquityData(
  series: Array<{ key: string; curve: EquityPoint[] }>
): ChartRow[] {
  const dateMap = new Map<string, Record<string, number>>();
  for (const { key, curve } of series) {
    for (const pt of curve) {
      if (!dateMap.has(pt.date)) dateMap.set(pt.date, {});
      dateMap.get(pt.date)![key] = pt.krw_value;
    }
  }
  return Array.from(dateMap.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, vals]) => ({ date, ...vals }));
}
