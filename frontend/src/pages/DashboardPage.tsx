import { useEffect, useState } from "react";
import type {
  DashboardSummaryResponse,
  AssetSummary,
  BacktestRunResponse,
  PriceDailyResponse,
} from "../types/api";
import { fetchDashboardSummary } from "../api/dashboard";
import { fetchPrices } from "../api/prices";
import Loading from "../components/common/Loading";
import ErrorMessage from "../components/common/ErrorMessage";
import MiniChart from "../components/charts/MiniChart";

/* ── 시그널 라벨 ── */
function signalLabel(action: string): { text: string; cls: string } {
  switch (action) {
    case "buy":
      return { text: "매수", cls: "bg-green-100 text-green-800" };
    case "sell":
      return { text: "청산", cls: "bg-red-100 text-red-800" };
    default:
      return { text: "관망", cls: "bg-gray-100 text-gray-600" };
  }
}

/* ── 가격 포맷 ── */
function fmtPrice(v: number | null): string {
  if (v == null) return "-";
  if (v >= 1_000) return v.toLocaleString("ko-KR", { maximumFractionDigits: 0 });
  return v.toFixed(2);
}

/* ── 등락률 포맷 ── */
function fmtChange(v: number | null): { text: string; cls: string } {
  if (v == null) return { text: "-", cls: "text-gray-400" };
  const sign = v > 0 ? "+" : "";
  const cls = v > 0 ? "text-green-600" : v < 0 ? "text-red-600" : "text-gray-600";
  return { text: `${sign}${v.toFixed(2)}%`, cls };
}

/* ── 전략 ID → 한글 ── */
const STRATEGY_NAMES: Record<string, string> = {
  momentum: "모멘텀",
  trend: "추세",
  mean_reversion: "평균회귀",
};

/* ── 최근 30일 날짜 ── */
function last30(): { start: string; end: string } {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - 45); // 영업일 고려 여유분
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null);
  const [miniPrices, setMiniPrices] = useState<Record<string, PriceDailyResponse[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    setError("");
    fetchDashboardSummary()
      .then(async (data) => {
        setSummary(data);
        // 미니차트용 최근 가격 병렬 fetch
        const { start, end } = last30();
        const entries = await Promise.all(
          data.assets.map(async (a) => {
            const prices = await fetchPrices({
              asset_id: a.asset_id,
              start_date: start,
              end_date: end,
              limit: 30,
            }).catch(() => []);
            return [a.asset_id, prices] as const;
          }),
        );
        setMiniPrices(Object.fromEntries(entries));
      })
      .catch((e) => setError(e.message || "요약 데이터를 불러올 수 없습니다"))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  if (loading) return <Loading message="대시보드 로딩 중..." />;
  if (error) return <ErrorMessage message={error} onRetry={load} />;
  if (!summary) return null;

  return (
    <div className="space-y-6">
      {/* ── 헤더 ── */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">대시보드</h2>
        <p className="text-sm text-gray-500 mt-1">
          7개 자산 요약 · 마지막 업데이트{" "}
          {new Date(summary.updated_at).toLocaleString("ko-KR")}
        </p>
      </div>

      {/* ── 자산 요약 카드 ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {summary.assets.map((asset) => (
          <AssetCard
            key={asset.asset_id}
            asset={asset}
            prices={miniPrices[asset.asset_id] || []}
          />
        ))}
      </div>

      {/* ── 최근 백테스트 ── */}
      {summary.recent_backtests.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3">
            최근 백테스트
          </h3>
          <BacktestTable runs={summary.recent_backtests} />
        </div>
      )}
    </div>
  );
}

/* ── 자산 카드 ── */
function AssetCard({
  asset,
  prices,
}: {
  asset: AssetSummary;
  prices: PriceDailyResponse[];
}) {
  const change = fmtChange(asset.price_change_pct);
  const chartData = prices
    .map((p) => ({ date: p.date, close: p.close }))
    .sort((a, b) => a.date.localeCompare(b.date));

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
      {/* 상단: 자산명 + 미니차트 */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500">{asset.asset_id}</p>
          <p className="text-sm font-semibold text-gray-900 mt-0.5">{asset.name}</p>
        </div>
        <MiniChart data={chartData} />
      </div>

      {/* 가격 + 등락률 */}
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-xl font-bold text-gray-900">
          {fmtPrice(asset.latest_price)}
        </span>
        <span className={`text-sm font-medium ${change.cls}`}>{change.text}</span>
      </div>

      {/* 시그널 배지 */}
      {asset.latest_signal && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {Object.entries(asset.latest_signal).map(([stratId, action]) => {
            const s = signalLabel(action);
            return (
              <span
                key={stratId}
                className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${s.cls}`}
              >
                {STRATEGY_NAMES[stratId] || stratId}: {s.text}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ── 백테스트 테이블 ── */
function BacktestTable({ runs }: { runs: BacktestRunResponse[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-left text-gray-600">
            <th className="py-2 pr-4">전략</th>
            <th className="py-2 pr-4">자산</th>
            <th className="py-2 pr-4">상태</th>
            <th className="py-2 pr-4">총수익률</th>
            <th className="py-2 pr-4">Sharpe</th>
            <th className="py-2 pr-4">MDD</th>
            <th className="py-2">실행일</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((r) => {
            const m = (r.metrics_json || {}) as Record<string, number>;
            return (
              <tr
                key={r.run_id}
                className="border-b border-gray-100 hover:bg-gray-50"
              >
                <td className="py-2 pr-4 font-medium">
                  {STRATEGY_NAMES[r.strategy_id] || r.strategy_id}
                </td>
                <td className="py-2 pr-4">{r.asset_id}</td>
                <td className="py-2 pr-4">
                  <span
                    className={`px-1.5 py-0.5 rounded text-xs ${
                      r.status === "success"
                        ? "bg-green-100 text-green-700"
                        : "bg-yellow-100 text-yellow-700"
                    }`}
                  >
                    {r.status === "success" ? "완료" : r.status}
                  </span>
                </td>
                <td className={`py-2 pr-4 ${metricColor(m.total_return_pct)}`}>
                  {m.total_return_pct != null
                    ? `${m.total_return_pct > 0 ? "+" : ""}${m.total_return_pct.toFixed(1)}%`
                    : "-"}
                </td>
                <td className="py-2 pr-4">
                  {m.sharpe_ratio != null ? m.sharpe_ratio.toFixed(2) : "-"}
                </td>
                <td className={`py-2 pr-4 ${metricColor(m.max_drawdown_pct, true)}`}>
                  {m.max_drawdown_pct != null
                    ? `${m.max_drawdown_pct.toFixed(1)}%`
                    : "-"}
                </td>
                <td className="py-2 text-gray-500">
                  {r.started_at
                    ? new Date(r.started_at).toLocaleDateString("ko-KR")
                    : "-"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function metricColor(v: number | undefined, invert = false): string {
  if (v == null) return "";
  const positive = invert ? v < 0 : v > 0;
  return positive ? "text-green-600" : v === 0 ? "" : "text-red-600";
}
