import { useState, useEffect, useCallback } from "react";
import { fetchBacktests, fetchEquity, fetchTrades } from "../api/backtests";
import type {
  BacktestRunResponse,
  EquityCurveResponse,
  TradeLogResponse,
} from "../types/api";
import EquityCurveChart from "../components/charts/EquityCurveChart";
import type { EquityPoint } from "../components/charts/EquityCurveChart";
import AssetSelect from "../components/common/AssetSelect";
import Loading from "../components/common/Loading";
import ErrorMessage from "../components/common/ErrorMessage";

const STRATEGIES = [
  { id: "momentum", label: "모멘텀" },
  { id: "trend_follow", label: "추세추종" },
  { id: "mean_reversion", label: "평균회귀" },
] as const;

/** metrics_json 에서 주요 메트릭 추출 */
interface Metrics {
  total_return: number | null;
  cagr: number | null;
  mdd: number | null;
  volatility: number | null;
  sharpe: number | null;
  sortino: number | null;
  calmar: number | null;
  win_rate: number | null;
  num_trades: number | null;
  avg_trade_pnl: number | null;
  bh_cagr: number | null;
  excess_return: number | null;
}

function parseMetrics(json: Record<string, unknown> | null): Metrics {
  if (!json) {
    return {
      total_return: null,
      cagr: null,
      mdd: null,
      volatility: null,
      sharpe: null,
      sortino: null,
      calmar: null,
      win_rate: null,
      num_trades: null,
      avg_trade_pnl: null,
      bh_cagr: null,
      excess_return: null,
    };
  }
  return {
    total_return: (json.total_return as number) ?? null,
    cagr: (json.cagr as number) ?? null,
    mdd: (json.mdd as number) ?? null,
    volatility: (json.volatility as number) ?? null,
    sharpe: (json.sharpe as number) ?? null,
    sortino: (json.sortino as number) ?? null,
    calmar: (json.calmar as number) ?? null,
    win_rate: (json.win_rate as number) ?? null,
    num_trades: (json.num_trades as number) ?? null,
    avg_trade_pnl: (json.avg_trade_pnl as number) ?? null,
    bh_cagr: (json.bh_cagr as number) ?? null,
    excess_return: (json.excess_return as number) ?? null,
  };
}

function pct(v: number | null): string {
  return v != null ? `${(v * 100).toFixed(2)}%` : "—";
}

function num2(v: number | null): string {
  return v != null ? v.toFixed(2) : "—";
}

function won(v: number | null): string {
  return v != null ? v.toLocaleString() : "—";
}

/** 에쿼티 커브 데이터를 date 기준으로 병합 */
function mergeEquityCurves(
  entries: { label: string; data: EquityCurveResponse[] }[],
): EquityPoint[] {
  const map = new Map<string, EquityPoint>();
  for (const { label, data } of entries) {
    for (const row of data) {
      let point = map.get(row.date);
      if (!point) {
        point = { date: row.date };
        map.set(row.date, point);
      }
      point[label] = row.equity;
    }
  }
  return Array.from(map.values()).sort((a, b) =>
    a.date.localeCompare(b.date),
  );
}

export default function StrategyPage() {
  const [assetId, setAssetId] = useState("KS200");
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([
    "momentum",
  ]);

  const [backtests, setBacktests] = useState<BacktestRunResponse[]>([]);
  const [equityData, setEquityData] = useState<EquityPoint[]>([]);
  const [equityLabels, setEquityLabels] = useState<string[]>([]);
  const [trades, setTrades] = useState<
    { label: string; trades: TradeLogResponse[] }[]
  >([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!assetId || selectedStrategies.length === 0) {
      setBacktests([]);
      setEquityData([]);
      setEquityLabels([]);
      setTrades([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      // 전략별 백테스트 목록 fetch (최신 1개씩)
      const btResults = await Promise.all(
        selectedStrategies.map((sid) =>
          fetchBacktests({ asset_id: assetId, strategy_id: sid, limit: 1 }),
        ),
      );
      const runs = btResults.flat().filter((r) => r.status === "success");
      setBacktests(runs);

      if (runs.length === 0) {
        setEquityData([]);
        setEquityLabels([]);
        setTrades([]);
        return;
      }

      // 에쿼티 커브 + 거래 이력 병렬 fetch
      const [equityResults, tradeResults] = await Promise.all([
        Promise.all(runs.map((r) => fetchEquity(r.run_id))),
        Promise.all(runs.map((r) => fetchTrades(r.run_id))),
      ]);

      const entries = runs.map((r, i) => ({
        label:
          STRATEGIES.find((s) => s.id === r.strategy_id)?.label ??
          r.strategy_id,
        data: equityResults[i],
      }));

      setEquityData(mergeEquityCurves(entries));
      setEquityLabels(entries.map((e) => e.label));
      setTrades(
        runs.map((r, i) => ({
          label:
            STRATEGIES.find((s) => s.id === r.strategy_id)?.label ??
            r.strategy_id,
          trades: tradeResults[i],
        })),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "데이터 로딩 실패");
    } finally {
      setLoading(false);
    }
  }, [assetId, selectedStrategies]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const toggleStrategy = (id: string) => {
    setSelectedStrategies((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id],
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">전략 성과 비교</h2>
        <p className="text-gray-500 mt-1 text-sm">
          에쿼티 커브, 성과 메트릭스, 거래 이력
        </p>
      </div>

      {/* 필터 영역 */}
      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            자산 선택
          </label>
          <AssetSelect value={assetId} onChange={setAssetId} />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            전략 선택
          </label>
          <div className="flex flex-wrap gap-2">
            {STRATEGIES.map((s) => {
              const selected = selectedStrategies.includes(s.id);
              return (
                <button
                  key={s.id}
                  onClick={() => toggleStrategy(s.id)}
                  className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                    selected
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
                  }`}
                >
                  {s.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 콘텐츠 */}
      {loading ? (
        <Loading message="백테스트 데이터 로딩 중..." />
      ) : error ? (
        <ErrorMessage message={error} onRetry={loadData} />
      ) : backtests.length === 0 ? (
        <div className="text-center text-gray-400 py-12">
          선택한 자산/전략에 대한 백테스트 결과가 없습니다
        </div>
      ) : (
        <div className="space-y-6">
          {/* 에쿼티 커브 */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">
              에쿼티 커브 — {assetId}
            </h3>
            <EquityCurveChart data={equityData} runLabels={equityLabels} />
          </div>

          {/* 성과 메트릭스 비교 테이블 */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700">
                성과 메트릭스
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">
                      지표
                    </th>
                    {backtests.map((bt) => (
                      <th
                        key={bt.run_id}
                        className="px-4 py-2 text-right text-xs font-medium text-gray-500"
                      >
                        {STRATEGIES.find((s) => s.id === bt.strategy_id)
                          ?.label ?? bt.strategy_id}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {[
                    {
                      label: "총수익률",
                      key: "total_return" as const,
                      fmt: pct,
                    },
                    { label: "CAGR", key: "cagr" as const, fmt: pct },
                    { label: "MDD", key: "mdd" as const, fmt: pct },
                    {
                      label: "변동성",
                      key: "volatility" as const,
                      fmt: pct,
                    },
                    {
                      label: "Sharpe",
                      key: "sharpe" as const,
                      fmt: num2,
                    },
                    {
                      label: "Sortino",
                      key: "sortino" as const,
                      fmt: num2,
                    },
                    {
                      label: "Calmar",
                      key: "calmar" as const,
                      fmt: num2,
                    },
                    { label: "승률", key: "win_rate" as const, fmt: pct },
                    {
                      label: "거래 횟수",
                      key: "num_trades" as const,
                      fmt: (v: number | null) =>
                        v != null ? v.toString() : "—",
                    },
                    {
                      label: "평균 거래 PnL",
                      key: "avg_trade_pnl" as const,
                      fmt: won,
                    },
                    {
                      label: "B&H CAGR",
                      key: "bh_cagr" as const,
                      fmt: pct,
                    },
                    {
                      label: "초과수익",
                      key: "excess_return" as const,
                      fmt: pct,
                    },
                  ].map((row) => (
                    <tr key={row.key} className="hover:bg-gray-50">
                      <td className="px-4 py-2 font-medium text-gray-700">
                        {row.label}
                      </td>
                      {backtests.map((bt) => {
                        const m = parseMetrics(bt.metrics_json);
                        const val = m[row.key];
                        const isNeg =
                          typeof val === "number" && val < 0;
                        return (
                          <td
                            key={bt.run_id}
                            className={`px-4 py-2 text-right tabular-nums ${
                              isNeg ? "text-red-600" : "text-gray-700"
                            }`}
                          >
                            {row.fmt(val)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 거래 이력 */}
          {trades.map(({ label, trades: tList }) => (
            <div
              key={label}
              className="bg-white rounded-lg border border-gray-200 overflow-hidden"
            >
              <div className="px-4 py-3 border-b border-gray-200">
                <h3 className="text-sm font-semibold text-gray-700">
                  거래 이력 — {label}
                </h3>
              </div>
              {tList.length === 0 ? (
                <div className="text-center text-gray-400 py-6 text-sm">
                  거래 내역 없음
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">
                          진입일
                        </th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                          진입가
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">
                          청산일
                        </th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                          청산가
                        </th>
                        <th className="px-3 py-2 text-center text-xs font-medium text-gray-500">
                          방향
                        </th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                          수량
                        </th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                          손익
                        </th>
                        <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                          수수료
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {tList.map((t) => {
                        const isProfit =
                          t.pnl != null && t.pnl > 0;
                        const isLoss =
                          t.pnl != null && t.pnl < 0;
                        return (
                          <tr key={t.id} className="hover:bg-gray-50">
                            <td className="px-3 py-2 text-gray-700 tabular-nums">
                              {t.entry_date}
                            </td>
                            <td className="px-3 py-2 text-right text-gray-700 tabular-nums">
                              {t.entry_price.toLocaleString()}
                            </td>
                            <td className="px-3 py-2 text-gray-700 tabular-nums">
                              {t.exit_date ?? "—"}
                            </td>
                            <td className="px-3 py-2 text-right text-gray-700 tabular-nums">
                              {t.exit_price != null
                                ? t.exit_price.toLocaleString()
                                : "—"}
                            </td>
                            <td className="px-3 py-2 text-center">
                              <span
                                className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                                  t.side === "long"
                                    ? "text-green-600 bg-green-50"
                                    : "text-red-600 bg-red-50"
                                }`}
                              >
                                {t.side === "long" ? "매수" : "매도"}
                              </span>
                            </td>
                            <td className="px-3 py-2 text-right text-gray-700 tabular-nums">
                              {t.shares.toLocaleString()}
                            </td>
                            <td
                              className={`px-3 py-2 text-right tabular-nums ${
                                isProfit
                                  ? "text-green-600"
                                  : isLoss
                                    ? "text-red-600"
                                    : "text-gray-700"
                              }`}
                            >
                              {t.pnl != null
                                ? t.pnl.toLocaleString()
                                : "—"}
                            </td>
                            <td className="px-3 py-2 text-right text-gray-500 tabular-nums">
                              {t.cost != null
                                ? t.cost.toLocaleString()
                                : "—"}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
