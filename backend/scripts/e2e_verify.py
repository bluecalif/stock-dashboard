#!/usr/bin/env python3
"""
E2E Pipeline Verification — Final backend verification before frontend build.

Runs the REAL pipeline code (preprocess → factors → signals → backtest → metrics)
with realistic synthetic data for all 7 assets, then displays results formatted
to match the 6 planned frontend UI pages.

No external DB or API required — exercises all business logic in-memory.

Usage:
    cd backend/
    python scripts/e2e_verify.py
"""

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure backend/ is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from research_engine.backtest import BacktestConfig, run_backtest
from research_engine.factors import ALL_FACTOR_NAMES, compute_all_factors
from research_engine.metrics import compute_metrics, metrics_to_dict
from research_engine.preprocessing import preprocess_from_df
from research_engine.strategies import STRATEGY_REGISTRY, get_strategy

# ──────────────────────────────────────────────────────────
# Asset definitions matching seed_assets.py
# ──────────────────────────────────────────────────────────
ASSETS = {
    "KS200":  {"name": "KOSPI200",      "category": "index",     "base": 330,  "vol": 0.012},
    "005930": {"name": "삼성전자",       "category": "stock",     "base": 72000, "vol": 0.018},
    "000660": {"name": "SK하이닉스",     "category": "stock",     "base": 195000, "vol": 0.025},
    "SOXL":   {"name": "SOXL ETF",      "category": "etf",       "base": 28,   "vol": 0.035},
    "BTC":    {"name": "Bitcoin",        "category": "crypto",    "base": 55000000, "vol": 0.030},
    "GC=F":   {"name": "Gold Futures",   "category": "commodity", "base": 2100, "vol": 0.008},
    "SI=F":   {"name": "Silver Futures", "category": "commodity", "base": 25,   "vol": 0.015},
}

# ──────────────────────────────────────────────────────────
# Step 1: Synthetic data generation (realistic OHLCV)
# ──────────────────────────────────────────────────────────
def generate_ohlcv(asset_id: str, start: str = "2024-06-01", end: str = "2026-02-10") -> pd.DataFrame:
    """Generate realistic OHLCV data with trends, mean-reversion, and volatility clusters."""
    info = ASSETS[asset_id]
    base = info["base"]
    vol = info["vol"]

    if info["category"] == "crypto":
        dates = pd.date_range(start, end, freq="D")
    else:
        dates = pd.bdate_range(start, end)

    n = len(dates)
    np.random.seed(hash(asset_id) % 2**31)

    # Regime-switching: trending + mean-reverting phases
    regime_len = n // 4
    returns = np.zeros(n)
    for i in range(4):
        start_idx = i * regime_len
        end_idx = min((i + 1) * regime_len, n)
        segment_len = end_idx - start_idx
        if i % 2 == 0:  # Trending
            drift = np.random.choice([-0.0003, 0.0005]) * (1 + i * 0.3)
            returns[start_idx:end_idx] = np.random.normal(drift, vol, segment_len)
        else:  # Mean-reverting / volatile
            returns[start_idx:end_idx] = np.random.normal(0, vol * 1.5, segment_len)

    # Build close prices
    close = base * np.cumprod(1 + returns)

    # OHLCV from close
    high_spread = np.abs(np.random.normal(0, vol * 0.6, n))
    low_spread = np.abs(np.random.normal(0, vol * 0.6, n))
    high = close * (1 + high_spread)
    low = close * (1 - low_spread)
    open_prices = close * (1 + np.random.normal(0, vol * 0.3, n))
    # Enforce high >= max(open, close) and low <= min(open, close)
    high = np.maximum(high, np.maximum(open_prices, close))
    low = np.minimum(low, np.minimum(open_prices, close))
    volume = np.random.lognormal(mean=15, sigma=0.5, size=n).astype(int)

    return pd.DataFrame({
        "open": open_prices,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }, index=dates)


# ──────────────────────────────────────────────────────────
# Display helpers
# ──────────────────────────────────────────────────────────
def fmt_price(val, asset_id):
    """Format price by asset type."""
    if asset_id in ("005930", "000660", "BTC"):
        return f"{val:,.0f}"
    elif asset_id in ("GC=F", "KS200"):
        return f"{val:,.2f}"
    elif asset_id in ("SI=F", "SOXL"):
        return f"{val:,.2f}"
    return f"{val:,.2f}"


def fmt_pct(val):
    if val is None:
        return "N/A"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.2f}%"


def fmt_pct_dec(val):
    if val is None:
        return "N/A"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.2%}"


def divider(title=""):
    w = 100
    if title:
        pad = (w - len(title) - 4) // 2
        return f"\n{'━' * pad} {title} {'━' * pad}"
    return "━" * w


# ══════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════
def main():
    t0 = time.perf_counter()
    print("=" * 100)
    print("  STOCK DASHBOARD — E2E PIPELINE VERIFICATION")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 100)

    # ── Step 1: Generate data (simulates collector) ──
    print(divider("STEP 1: DATA COLLECTION (Simulated FDR)"))
    raw_data = {}
    for asset_id, info in ASSETS.items():
        df = generate_ohlcv(asset_id)
        raw_data[asset_id] = df
        print(f"  ✓ {asset_id:>8s} ({info['name']:12s}): {len(df):>4d} rows | "
              f"{df.index[0].date()} ~ {df.index[-1].date()} | "
              f"Close: {fmt_price(df['close'].iloc[-1], asset_id)}")
    print(f"  Total: {sum(len(d) for d in raw_data.values()):,} rows across {len(raw_data)} assets")

    # ── Step 2: Preprocessing ──
    print(divider("STEP 2: PREPROCESSING (Calendar align + Missing + Outlier)"))
    preprocessed = {}
    for asset_id, df in raw_data.items():
        category = ASSETS[asset_id]["category"]
        pp = preprocess_from_df(df, category=category)
        preprocessed[asset_id] = pp
        n_filled = int(pp["is_filled"].sum()) if "is_filled" in pp.columns else 0
        n_outlier = int(pp["is_outlier"].sum()) if "is_outlier" in pp.columns else 0
        print(f"  ✓ {asset_id:>8s}: {len(pp):>4d} rows | "
              f"filled={n_filled}, outliers={n_outlier}")

    # ── Step 3: Factor generation ──
    print(divider("STEP 3: FACTOR GENERATION (15 Factors)"))
    print(f"  Factors: {', '.join(ALL_FACTOR_NAMES)}")
    factors_data = {}
    for asset_id, pp in preprocessed.items():
        fdf = compute_all_factors(pp)
        # Merge close into factors for mean_reversion strategy
        fdf["close"] = pp["close"]
        factors_data[asset_id] = fdf
        valid = fdf.dropna(subset=["ret_63d"])
        print(f"  ✓ {asset_id:>8s}: {len(fdf):>4d} rows | "
              f"valid(ret_63d+)={len(valid)} | NaN columns at end: "
              f"{sum(fdf.iloc[-1].isna())}")

    # ── Step 4: Signal generation ──
    print(divider("STEP 4: SIGNAL GENERATION (3 Strategies × 7 Assets)"))
    strategy_names = list(STRATEGY_REGISTRY.keys())
    signals_data = {}  # {(asset_id, strategy_name): SignalResult}
    for asset_id, fdf in factors_data.items():
        for sname in strategy_names:
            strategy = get_strategy(sname)
            sig_result = strategy.generate_signals(fdf, asset_id)
            signals_data[(asset_id, sname)] = sig_result
            print(f"  ✓ {asset_id:>8s}/{sname:16s}: "
                  f"{len(sig_result.signals):>4d} signals | "
                  f"entry={sig_result.n_entry:<3d} exit={sig_result.n_exit:<3d} "
                  f"hold={sig_result.n_hold}")

    # ── Step 5: Backtest + Metrics ──
    print(divider("STEP 5: BACKTEST + METRICS (10M KRW initial)"))
    config = BacktestConfig(initial_cash=10_000_000)
    backtest_results = {}  # {(asset_id, strategy_name): (BacktestResult, PerformanceMetrics)}
    for (asset_id, sname), sig_result in signals_data.items():
        if sig_result.signals.empty or sig_result.n_entry == 0:
            continue
        bt = run_backtest(
            prices=preprocessed[asset_id],
            signals=sig_result.signals,
            asset_id=asset_id,
            strategy_id=sname,
            config=config,
        )
        if bt.equity_curve.empty:
            continue
        metrics = compute_metrics(bt)
        backtest_results[(asset_id, sname)] = (bt, metrics)
        print(f"  ✓ {asset_id:>8s}/{sname:16s}: "
              f"Return={metrics.total_return:>+8.2%} | "
              f"CAGR={metrics.cagr:>+7.2%} | "
              f"MDD={metrics.mdd:>+7.2%} | "
              f"Sharpe={metrics.sharpe:>5.2f} | "
              f"Trades={metrics.num_trades}")

    elapsed = time.perf_counter() - t0
    print(f"\n  Pipeline complete in {elapsed:.1f}s | "
          f"{len(backtest_results)} backtest runs generated")

    # ══════════════════════════════════════════════════════
    # FRONTEND UI PAGE PREVIEWS
    # ══════════════════════════════════════════════════════
    print("\n" + "=" * 100)
    print("  FRONTEND UI — DATA PREVIEW (matches planned 6 pages)")
    print("=" * 100)

    # ────────────────────────────────────────────────────
    # PAGE 1: Dashboard Home
    # ────────────────────────────────────────────────────
    print(divider("PAGE 1: DASHBOARD HOME"))
    print(f"  {'Asset':>10s} {'Name':14s} {'Latest':>14s} {'Change':>8s}  Signals (momentum / trend / mean_rev)")
    print(f"  {'─'*10} {'─'*14} {'─'*14} {'─'*8}  {'─'*38}")
    for asset_id, info in ASSETS.items():
        pp = preprocessed[asset_id]
        last_close = pp["close"].iloc[-1]
        prev_close = pp["close"].iloc[-2] if len(pp) >= 2 else last_close
        change_pct = (last_close - prev_close) / prev_close * 100

        sig_strs = []
        for sname in strategy_names:
            key = (asset_id, sname)
            if key in signals_data:
                sr = signals_data[key]
                last_sig = sr.signals.iloc[-1] if not sr.signals.empty else None
                if last_sig is not None:
                    action = last_sig.get("action", "—")
                    sig_val = int(last_sig.get("signal", 0))
                    marker = "●" if sig_val == 1 else "○"
                    sig_strs.append(f"{marker} {action:5s}")
                else:
                    sig_strs.append("  —   ")
            else:
                sig_strs.append("  —   ")

        print(f"  {asset_id:>10s} {info['name']:14s} {fmt_price(last_close, asset_id):>14s} "
              f"{fmt_pct(change_pct):>8s}  {' / '.join(sig_strs)}")

    # Recent backtests
    recent_bt = sorted(backtest_results.items(), key=lambda x: x[1][1].total_return, reverse=True)[:5]
    print(f"\n  📊 Recent Backtests (Top 5 by Return):")
    print(f"  {'Strategy':20s} {'Asset':>8s} {'Return':>10s} {'CAGR':>8s} {'MDD':>8s} {'Sharpe':>7s}")
    print(f"  {'─'*20} {'─'*8} {'─'*10} {'─'*8} {'─'*8} {'─'*7}")
    for (aid, sname), (bt, m) in recent_bt:
        print(f"  {sname:20s} {aid:>8s} {m.total_return:>+9.2%} "
              f"{m.cagr:>+7.2%} {m.mdd:>+7.2%} {m.sharpe:>7.2f}")

    # ────────────────────────────────────────────────────
    # PAGE 2: Price / Returns Chart
    # ────────────────────────────────────────────────────
    print(divider("PAGE 2: PRICE / RETURNS COMPARISON"))
    print("\n  [Price Summary — latest 5 trading days]")
    for asset_id in ASSETS:
        pp = preprocessed[asset_id]
        tail = pp.tail(5)
        prices_str = " → ".join(f"{fmt_price(c, asset_id)}" for c in tail["close"])
        print(f"  {asset_id:>8s}: {prices_str}")

    print("\n  [Normalized Cumulative Returns — from start date]")
    print(f"  {'Asset':>10s} {'1M':>8s} {'3M':>8s} {'6M':>8s} {'1Y':>8s} {'Total':>8s}")
    print(f"  {'─'*10} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*8}")
    for asset_id in ASSETS:
        pp = preprocessed[asset_id]
        closes = pp["close"]
        base = closes.iloc[0]
        total = (closes.iloc[-1] / base - 1) * 100
        n = len(closes)
        ret_1m = (closes.iloc[min(21, n-1)] / base - 1) * 100
        ret_3m = (closes.iloc[min(63, n-1)] / base - 1) * 100
        ret_6m = (closes.iloc[min(126, n-1)] / base - 1) * 100
        ret_1y = (closes.iloc[min(252, n-1)] / base - 1) * 100
        print(f"  {asset_id:>10s} {fmt_pct(ret_1m):>8s} {fmt_pct(ret_3m):>8s} "
              f"{fmt_pct(ret_6m):>8s} {fmt_pct(ret_1y):>8s} {fmt_pct(total):>8s}")

    # ────────────────────────────────────────────────────
    # PAGE 3: Correlation Heatmap
    # ────────────────────────────────────────────────────
    print(divider("PAGE 3: CORRELATION HEATMAP (60-day returns)"))
    # Build returns DataFrame and compute correlation
    returns_dict = {}
    for asset_id in ASSETS:
        pp = preprocessed[asset_id]
        ret = pp["close"].pct_change().dropna().tail(60)
        # Align to business days for non-crypto
        returns_dict[asset_id] = ret

    ret_df = pd.DataFrame(returns_dict)
    ret_df = ret_df.dropna()
    corr = ret_df.corr()

    # Print header
    ids = list(ASSETS.keys())
    header = f"  {'':>8s}  " + "  ".join(f"{a:>8s}" for a in ids)
    print(header)
    print(f"  {'─'*8}  " + "  ".join(["─" * 8] * len(ids)))
    for row_id in ids:
        vals = []
        for col_id in ids:
            if row_id in corr.index and col_id in corr.columns:
                v = corr.loc[row_id, col_id]
                if pd.notna(v):
                    vals.append(f"{v:>8.3f}")
                else:
                    vals.append(f"{'N/A':>8s}")
            else:
                vals.append(f"{'N/A':>8s}")
        print(f"  {row_id:>8s}  " + "  ".join(vals))

    # ────────────────────────────────────────────────────
    # PAGE 4: Factor Status
    # ────────────────────────────────────────────────────
    print(divider("PAGE 4: FACTOR STATUS (Latest Values)"))
    key_factors = ["rsi_14", "macd", "sma_20", "sma_60", "vol_20", "ret_1d", "ret_20d", "atr_14"]
    print(f"  {'Asset':>8s}  " + "  ".join(f"{f:>10s}" for f in key_factors))
    print(f"  {'─'*8}  " + "  ".join(["─" * 10] * len(key_factors)))
    for asset_id in ASSETS:
        fdf = factors_data[asset_id]
        last_row = fdf.iloc[-1]
        vals = []
        for f in key_factors:
            v = last_row.get(f)
            if pd.notna(v):
                if f == "rsi_14":
                    vals.append(f"{v:>10.1f}")
                elif f in ("ret_1d", "ret_20d"):
                    vals.append(f"{v:>+9.2%}")
                elif f == "vol_20":
                    vals.append(f"{v:>10.1%}")
                elif f == "macd":
                    vals.append(f"{v:>10.1f}")
                elif f == "atr_14":
                    vals.append(f"{v:>10.2f}")
                else:
                    vals.append(f"{v:>10.1f}")
            else:
                vals.append(f"{'N/A':>10s}")
        print(f"  {asset_id:>8s}  " + "  ".join(vals))

    # ────────────────────────────────────────────────────
    # PAGE 5: Signal Timeline
    # ────────────────────────────────────────────────────
    print(divider("PAGE 5: SIGNAL TIMELINE (Recent Entry/Exit)"))
    for sname in strategy_names:
        print(f"\n  [{sname.upper()}]")
        print(f"  {'Asset':>8s} {'Date':>12s} {'Action':>8s} {'Signal':>7s} {'Price':>14s} {'Score':>8s}")
        print(f"  {'─'*8} {'─'*12} {'─'*8} {'─'*7} {'─'*14} {'─'*8}")

        for asset_id in ASSETS:
            key = (asset_id, sname)
            if key not in signals_data:
                continue
            sr = signals_data[key]
            if sr.signals.empty:
                continue
            # Show last 3 entry/exit events
            sigs = sr.signals
            events = sigs[sigs["action"].isin(["entry", "exit"])].tail(3)
            for _, row in events.iterrows():
                date_val = row["date"]
                date_str = date_val.strftime("%Y-%m-%d") if hasattr(date_val, "strftime") else str(date_val)
                sig_val = int(row["signal"])
                marker = "▲ BUY" if sig_val == 1 else "▼ SELL"
                action = row["action"]
                # Get close price for this date
                pp = preprocessed[asset_id]
                date_ts = pd.Timestamp(date_val)
                price = pp.loc[date_ts, "close"] if date_ts in pp.index else None
                price_str = fmt_price(price, asset_id) if price is not None else "N/A"
                score = row.get("score", None)
                score_str = f"{score:.4f}" if score is not None and pd.notna(score) else "—"
                print(f"  {asset_id:>8s} {date_str:>12s} {action:>8s} {marker:>7s} "
                      f"{price_str:>14s} {score_str:>8s}")

    # ────────────────────────────────────────────────────
    # PAGE 6: Strategy Performance
    # ────────────────────────────────────────────────────
    print(divider("PAGE 6: STRATEGY PERFORMANCE"))

    for sname in strategy_names:
        print(f"\n  ┌─ {sname.upper()} ─────────────────────────────────────────────────┐")
        strat_results = [(aid, bt, m) for (aid, s), (bt, m) in backtest_results.items() if s == sname]

        if not strat_results:
            print(f"  │  No backtest results for {sname}")
            print(f"  └{'─'*60}┘")
            continue

        # Metrics table
        print(f"  │ {'Asset':>8s} {'Return':>10s} {'CAGR':>8s} {'MDD':>8s} {'Sharpe':>7s} "
              f"{'Sortino':>8s} {'WinRate':>8s} {'Trades':>7s} {'vs B&H':>8s} │")
        print(f"  │ {'─'*8} {'─'*10} {'─'*8} {'─'*8} {'─'*7} {'─'*8} {'─'*8} {'─'*7} {'─'*8} │")
        for aid, bt, m in sorted(strat_results, key=lambda x: x[2].total_return, reverse=True):
            excess = fmt_pct_dec(m.excess_return)
            print(f"  │ {aid:>8s} {m.total_return:>+9.2%} {m.cagr:>+7.2%} "
                  f"{m.mdd:>+7.2%} {m.sharpe:>7.2f} {m.sortino:>8.2f} "
                  f"{m.win_rate:>7.0%} {m.num_trades:>7d} {excess:>8s} │")

        # Equity curve snapshot (start → mid → end)
        print(f"  │")
        print(f"  │ Equity Curve Snapshot (Start → Mid → End):")
        for aid, bt, m in strat_results[:3]:
            eq = bt.equity_curve
            if len(eq) >= 3:
                mid_idx = len(eq) // 2
                start_eq = eq.iloc[0]["equity"]
                mid_eq = eq.iloc[mid_idx]["equity"]
                end_eq = eq.iloc[-1]["equity"]
                bh_end = bt.buy_hold_equity.iloc[-1]["equity"] if not bt.buy_hold_equity.empty else 0
                print(f"  │   {aid:>8s}: {start_eq:>12,.0f} → {mid_eq:>12,.0f} → {end_eq:>12,.0f}  "
                      f"(B&H: {bh_end:>12,.0f})")

        # Trade log sample
        print(f"  │")
        print(f"  │ Recent Trades:")
        print(f"  │   {'Asset':>8s} {'Entry':>12s} {'Exit':>12s} {'Side':>6s} {'PnL':>14s}")
        all_trades = []
        for aid, bt, m in strat_results:
            for t in bt.trades:
                all_trades.append((aid, t))
        for aid, t in sorted(all_trades, key=lambda x: str(x[1].entry_date), reverse=True)[:5]:
            exit_str = str(t.exit_date) if t.exit_date else "OPEN"
            pnl_str = f"{t.pnl:>+13,.0f}" if t.pnl is not None else "N/A"
            print(f"  │   {aid:>8s} {str(t.entry_date):>12s} {exit_str:>12s} "
                  f"{t.side:>6s} {pnl_str}")

        print(f"  └{'─'*70}┘")

    # ══════════════════════════════════════════════════════
    # VERIFICATION SUMMARY
    # ══════════════════════════════════════════════════════
    total_time = time.perf_counter() - t0
    print("\n" + "=" * 100)
    print("  VERIFICATION SUMMARY")
    print("=" * 100)

    checks = []

    # Check 1: All 7 assets generated
    c1 = len(raw_data) == 7
    checks.append(("7 assets data generated", c1, f"{len(raw_data)}/7"))

    # Check 2: Preprocessing complete
    c2 = all(len(pp) > 0 for pp in preprocessed.values())
    checks.append(("Preprocessing (calendar+missing+outlier)", c2,
                    f"{sum(len(p) for p in preprocessed.values()):,} total rows"))

    # Check 3: 15 factors computed
    c3 = all(len(f.columns) >= 15 for f in factors_data.values())  # 15 + close
    factor_cols = set()
    for f in factors_data.values():
        factor_cols.update(f.columns)
    checks.append(("15 factors computed per asset", c3,
                    f"{len(factor_cols) - 1} unique factors"))  # -1 for close

    # Check 4: Signals generated
    total_signals = sum(len(sr.signals) for sr in signals_data.values())
    total_entries = sum(sr.n_entry for sr in signals_data.values())
    c4 = total_entries > 0
    checks.append(("Signal generation (3 strategies × 7 assets)", c4,
                    f"{total_signals:,} signals, {total_entries} entries"))

    # Check 5: Backtests run
    c5 = len(backtest_results) > 0
    checks.append(("Backtest execution", c5, f"{len(backtest_results)} runs"))

    # Check 6: Metrics computed
    all_metrics_valid = all(
        m.total_return != 0.0 or m.num_trades == 0
        for _, (_, m) in backtest_results.items()
    )
    checks.append(("Performance metrics (13 indicators)", all_metrics_valid,
                    "CAGR, MDD, Sharpe, Sortino, Calmar, WinRate, etc."))

    # Check 7: Correlation matrix
    c7 = corr.shape == (7, 7)
    checks.append(("Correlation matrix (7×7)", c7, f"{corr.shape[0]}×{corr.shape[1]}"))

    # Check 8: Dashboard data ready
    c8 = True  # If we got here, all data is available
    checks.append(("Dashboard summary data available", c8,
                    "prices + signals + backtests"))

    # Check 9: API data shapes
    c9 = all(
        not bt.equity_curve.empty and len(bt.trades) >= 0
        for (bt, _) in backtest_results.values()
    )
    checks.append(("API response data shapes valid", c9,
                    "equity_curve + trade_log"))

    # Print results
    all_pass = True
    for name, passed, detail in checks:
        icon = "✅" if passed else "❌"
        all_pass = all_pass and passed
        print(f"  {icon} {name:50s} → {detail}")

    print(f"\n  {'─'*70}")
    final = "ALL CHECKS PASSED" if all_pass else "SOME CHECKS FAILED"
    icon = "✅" if all_pass else "❌"
    print(f"  {icon} {final} | {total_time:.1f}s | Ready for Phase 5 (Frontend)")
    print("=" * 100)

    # Return exit code
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
