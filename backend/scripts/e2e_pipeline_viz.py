"""E2E Pipeline Verification & Visualization.

Runs the full pipeline: DB check → Collect → Factors → Signals → Backtest → Visualize.
Generates a comprehensive multi-panel dashboard image for final backend verification.
"""

import sys
import time
from datetime import date
from pathlib import Path

# Ensure backend/ is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# Pipeline modules
from collector.ingest import ingest_asset
from config.logging import setup_logging
from db.models import AssetMaster, BacktestRun, FactorDaily, PriceDaily, SignalDaily
from db.session import SessionLocal
from research_engine.backtest import BacktestConfig, run_backtest
from research_engine.factor_store import store_factors_for_asset
from research_engine.factors import compute_all_factors
from research_engine.metrics import compute_metrics, metrics_to_dict
from research_engine.preprocessing import preprocess
from research_engine.signal_store import store_signals_for_asset
from research_engine.strategies import STRATEGY_REGISTRY

# ──────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────
START = "2023-06-01"
END = date.today().strftime("%Y-%m-%d")
STRATEGIES = list(STRATEGY_REGISTRY.keys())  # momentum, trend, mean_reversion
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "e2e_report"

# Asset display names for charts
ASSET_LABELS = {
    "KS200": "KOSPI200",
    "005930": "Samsung",
    "000660": "SK Hynix",
    "SOXL": "SOXL",
    "BTC": "BTC",
    "GC=F": "Gold",
    "SI=F": "Silver",
}

# Color palette
COLORS = {
    "KS200": "#1f77b4",
    "005930": "#ff7f0e",
    "000660": "#2ca02c",
    "SOXL": "#d62728",
    "BTC": "#9467bd",
    "GC=F": "#e6c300",
    "SI=F": "#7f7f7f",
}

STRATEGY_COLORS = {
    "momentum": "#e74c3c",
    "trend": "#3498db",
    "mean_reversion": "#2ecc71",
}


def banner(msg: str):
    print(f"\n{'='*70}")
    print(f"  {msg}")
    print(f"{'='*70}")


def section(msg: str):
    print(f"\n--- {msg} ---")


# ──────────────────────────────────────────────────────────────
# Step 1: DB Status
# ──────────────────────────────────────────────────────────────
def check_db(session) -> dict:
    banner("STEP 1: Database Status Check")

    assets = session.query(AssetMaster).filter(AssetMaster.is_active.is_(True)).all()
    asset_ids = [a.asset_id for a in assets]
    print(f"  Active assets: {len(asset_ids)} → {asset_ids}")

    price_count = session.query(PriceDaily).count()
    print(f"  Total price_daily rows: {price_count:,}")

    # Per-asset price range
    from sqlalchemy import func
    for aid in asset_ids:
        stats = session.query(
            func.min(PriceDaily.date),
            func.max(PriceDaily.date),
            func.count(PriceDaily.date),
        ).filter(PriceDaily.asset_id == aid).first()
        if stats[0]:
            print(f"    {aid:>8}: {stats[0]} ~ {stats[1]}  ({stats[2]:,} rows)")

    factor_count = session.query(FactorDaily).count()
    signal_count = session.query(SignalDaily).count()
    bt_count = session.query(BacktestRun).count()
    print(f"  factor_daily rows: {factor_count:,}")
    print(f"  signal_daily rows: {signal_count:,}")
    print(f"  backtest_run rows: {bt_count}")

    return {"asset_ids": asset_ids, "price_count": price_count}


# ──────────────────────────────────────────────────────────────
# Step 2: Data Collection
# ──────────────────────────────────────────────────────────────
def collect_data(session, asset_ids: list[str]) -> dict:
    banner("STEP 2: Data Collection (FDR)")
    results = {}
    for aid in asset_ids:
        section(f"Collecting {aid}")
        t0 = time.perf_counter()
        r = ingest_asset(aid, START, END, session)
        elapsed = time.perf_counter() - t0
        results[aid] = r
        status = "OK" if r.status == "success" else "FAIL"
        print(f"  [{status}] {aid}: {r.row_count} rows ({elapsed:.1f}s)")
        if r.status != "success":
            print(f"    Error: {r.errors}")

    ok = sum(1 for r in results.values() if r.status == "success")
    print(f"\n  Summary: {ok}/{len(asset_ids)} assets collected successfully")
    return results


# ──────────────────────────────────────────────────────────────
# Step 3: Factor Generation
# ──────────────────────────────────────────────────────────────
def generate_factors(session, asset_ids: list[str]) -> dict:
    banner("STEP 3: Factor Generation (15 indicators)")
    results = {}
    for aid in asset_ids:
        section(f"Computing factors for {aid}")
        r = store_factors_for_asset(session, aid, START, END)
        results[aid] = r
        status = "OK" if r.status == "success" else "FAIL"
        print(f"  [{status}] {aid}: {r.row_count} factor rows, "
              f"{r.factor_count} factors ({r.elapsed_ms:.0f}ms)")
    return results


# ──────────────────────────────────────────────────────────────
# Step 4: Signal Generation
# ──────────────────────────────────────────────────────────────
def generate_signals(session, asset_ids: list[str]) -> tuple[dict, list[str]]:
    banner("STEP 4: Signal Generation (3 strategies)")
    all_results = {}
    valid_ids = []
    for aid in asset_ids:
        try:
            df_pre = preprocess(session, aid, START, END, missing_threshold=0.10)
        except ValueError as e:
            print(f"  [SKIP] {aid}: {e}")
            continue
        df_factors = compute_all_factors(df_pre)
        # Include close for mean_reversion strategy
        df_factors["close"] = df_pre["close"]
        asset_results = {}
        for strat in STRATEGIES:
            r = store_signals_for_asset(session, aid, strat, df_factors)
            asset_results[strat] = r
            print(f"  {aid}/{strat}: {r.row_count} signals "
                  f"(entry={r.n_entry}, exit={r.n_exit})")
        all_results[aid] = asset_results
        valid_ids.append(aid)
    return all_results, valid_ids


# ──────────────────────────────────────────────────────────────
# Step 5: Backtesting
# ──────────────────────────────────────────────────────────────
def run_backtests(session, asset_ids: list[str]) -> dict:
    banner("STEP 5: Backtesting (all assets × all strategies)")
    config = BacktestConfig(initial_cash=10_000_000)
    all_results = {}

    for aid in asset_ids:
        try:
            df_pre = preprocess(session, aid, START, END, missing_threshold=0.10)
        except ValueError as e:
            print(f"  [SKIP] {aid}: {e}")
            continue
        df_factors = compute_all_factors(df_pre)
        df_factors["close"] = df_pre["close"]
        asset_results = {}

        for strat in STRATEGIES:
            sig_rows = (
                session.query(SignalDaily)
                .filter(SignalDaily.asset_id == aid, SignalDaily.strategy_id == strat)
                .all()
            )
            signals_df = pd.DataFrame(
                [{"date": r.date, "signal": r.signal} for r in sig_rows]
            )
            if signals_df.empty:
                print(f"  {aid}/{strat}: No signals, skipping backtest")
                continue

            bt = run_backtest(df_pre, signals_df, aid, strat, config)
            metrics = compute_metrics(bt)

            asset_results[strat] = {
                "backtest": bt,
                "metrics": metrics,
                "metrics_dict": metrics_to_dict(metrics),
            }
            print(f"  {aid}/{strat}: CAGR={metrics.cagr:+.1%}, "
                  f"MDD={metrics.mdd:.1%}, Sharpe={metrics.sharpe:.2f}, "
                  f"trades={metrics.num_trades}, WR={metrics.win_rate:.0%}")

        all_results[aid] = asset_results

    return all_results


# ──────────────────────────────────────────────────────────────
# Step 6: Visualization
# ──────────────────────────────────────────────────────────────
def visualize_all(session, asset_ids: list[str], bt_results: dict):
    banner("STEP 6: Generating Visualization Dashboard")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Use a clean style
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "figure.dpi": 150,
    })

    # ── Panel 1: Price Chart (Normalized) ──
    _plot_normalized_prices(session, asset_ids)

    # ── Panel 2: Correlation Heatmap ──
    _plot_correlation(session, asset_ids)

    # ── Panel 3: Backtest Equity Curves (per strategy) ──
    _plot_equity_curves(bt_results, asset_ids)

    # ── Panel 4: Strategy Performance Comparison ──
    _plot_strategy_comparison(bt_results, asset_ids)

    # ── Panel 5: Combined Dashboard ──
    _plot_combined_dashboard(session, asset_ids, bt_results)

    print(f"\n  All charts saved to: {OUTPUT_DIR}")


def _load_prices_df(session, asset_ids: list[str]) -> dict[str, pd.DataFrame]:
    """Load price data from DB for visualization."""
    price_data = {}
    for aid in asset_ids:
        rows = (
            session.query(PriceDaily)
            .filter(PriceDaily.asset_id == aid, PriceDaily.date >= START)
            .order_by(PriceDaily.date)
            .all()
        )
        if rows:
            df = pd.DataFrame([{
                "date": r.date, "close": float(r.close),
                "open": float(r.open), "high": float(r.high),
                "low": float(r.low), "volume": int(r.volume),
            } for r in rows])
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
            price_data[aid] = df
    return price_data


def _plot_normalized_prices(session, asset_ids: list[str]):
    """Panel 1: Normalized price comparison (base=100)."""
    price_data = _load_prices_df(session, asset_ids)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), height_ratios=[3, 1])
    fig.suptitle("Asset Price Performance (Normalized, Base=100)", fontsize=14, fontweight="bold")

    for aid in asset_ids:
        if aid not in price_data:
            continue
        df = price_data[aid]
        normalized = df["close"] / df["close"].iloc[0] * 100
        label = ASSET_LABELS.get(aid, aid)
        ax1.plot(normalized.index, normalized.values,
                 label=label, color=COLORS.get(aid, None), linewidth=1.2, alpha=0.9)

    ax1.axhline(y=100, color="gray", linestyle="--", alpha=0.5, linewidth=0.8)
    ax1.set_ylabel("Normalized Price (Base=100)")
    ax1.legend(loc="upper left", ncol=4, framealpha=0.9)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))

    # Volume subplot for a major asset (Samsung)
    vol_aid = "005930" if "005930" in price_data else asset_ids[0]
    if vol_aid in price_data:
        df = price_data[vol_aid]
        ax2.bar(df.index, df["volume"], color=COLORS.get(vol_aid, "#888"), alpha=0.4, width=1)
        ax2.set_ylabel(f"Volume ({ASSET_LABELS.get(vol_aid, vol_aid)})")
        ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e6:.0f}M"))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "1_price_normalized.png", bbox_inches="tight")
    plt.close(fig)
    print("  [1/5] Price chart saved")


def _plot_correlation(session, asset_ids: list[str]):
    """Panel 2: Return correlation heatmap."""
    price_data = _load_prices_df(session, asset_ids)

    returns = pd.DataFrame()
    for aid in asset_ids:
        if aid in price_data:
            label = ASSET_LABELS.get(aid, aid)
            returns[label] = price_data[aid]["close"].pct_change()

    corr = returns.dropna().corr()

    fig, ax = plt.subplots(figsize=(8, 7))
    fig.suptitle("Asset Return Correlation Matrix", fontsize=14, fontweight="bold")

    np.triu(np.ones_like(corr, dtype=bool), k=1)
    n = len(corr)

    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")

    # Show values
    for i in range(n):
        for j in range(n):
            val = corr.values[i, j]
            color = "white" if abs(val) > 0.6 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=10, fontweight="bold", color=color)

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr.index)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Correlation")

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "2_correlation_heatmap.png", bbox_inches="tight")
    plt.close(fig)
    print("  [2/5] Correlation heatmap saved")


def _plot_equity_curves(bt_results: dict, asset_ids: list[str]):
    """Panel 3: Equity curves per strategy."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle(
        "Backtest Equity Curves by Strategy (Initial: 10M KRW)",
        fontsize=14, fontweight="bold",
    )

    for idx, strat in enumerate(STRATEGIES):
        ax = axes[idx]
        ax.set_title(strat.replace("_", " ").title(), fontsize=12, fontweight="bold")
        has_data = False

        for aid in asset_ids:
            if aid not in bt_results or strat not in bt_results[aid]:
                continue
            bt = bt_results[aid][strat]["backtest"]
            eq = bt.equity_curve
            if eq.empty:
                continue
            has_data = True
            label = ASSET_LABELS.get(aid, aid)
            dates = pd.to_datetime(eq["date"])
            ax.plot(dates, eq["equity"], label=label,
                    color=COLORS.get(aid, None), linewidth=1.0, alpha=0.85)

        ax.axhline(y=10_000_000, color="gray", linestyle="--", alpha=0.5, linewidth=0.8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e6:.0f}M"))
        ax.set_ylabel("Equity (KRW)")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%y-%m"))
        if has_data:
            ax.legend(loc="upper left", fontsize=7, ncol=2)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "3_equity_curves.png", bbox_inches="tight")
    plt.close(fig)
    print("  [3/5] Equity curves saved")


def _plot_strategy_comparison(bt_results: dict, asset_ids: list[str]):
    """Panel 4: Strategy performance metrics comparison."""
    # Build metrics table
    rows = []
    for aid in asset_ids:
        if aid not in bt_results:
            continue
        for strat in STRATEGIES:
            if strat not in bt_results[aid]:
                continue
            m = bt_results[aid][strat]["metrics"]
            rows.append({
                "asset": ASSET_LABELS.get(aid, aid),
                "asset_id": aid,
                "strategy": strat,
                "CAGR": m.cagr * 100,
                "MDD": m.mdd * 100,
                "Sharpe": m.sharpe,
                "Win Rate": m.win_rate * 100,
                "Trades": m.num_trades,
                "Total Return": m.total_return * 100,
                "Excess vs BH": (m.excess_return or 0) * 100,
            })

    if not rows:
        print("  [4/5] No backtest data for comparison chart")
        return

    df = pd.DataFrame(rows)

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("Strategy Performance Comparison", fontsize=14, fontweight="bold")

    # 4a: CAGR by asset × strategy
    ax = axes[0, 0]
    _grouped_bar(ax, df, "CAGR", "CAGR (%)", asset_ids)
    ax.axhline(y=0, color="black", linewidth=0.5)

    # 4b: MDD by asset × strategy
    ax = axes[0, 1]
    _grouped_bar(ax, df, "MDD", "Max Drawdown (%)", asset_ids)

    # 4c: Sharpe by asset × strategy
    ax = axes[1, 0]
    _grouped_bar(ax, df, "Sharpe", "Sharpe Ratio", asset_ids)
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.axhline(y=1, color="green", linestyle="--", alpha=0.3, linewidth=0.8)

    # 4d: Excess return vs Buy & Hold
    ax = axes[1, 1]
    _grouped_bar(ax, df, "Excess vs BH", "Excess Return vs B&H (%)", asset_ids)
    ax.axhline(y=0, color="black", linewidth=0.5)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "4_strategy_comparison.png", bbox_inches="tight")
    plt.close(fig)
    print("  [4/5] Strategy comparison saved")


def _grouped_bar(ax, df, metric: str, ylabel: str, asset_ids: list[str]):
    """Helper: draw grouped bar chart (assets × strategies)."""
    x_labels = [ASSET_LABELS.get(aid, aid) for aid in asset_ids
                if aid in df["asset_id"].values]
    n_groups = len(x_labels)
    n_strats = len(STRATEGIES)
    bar_width = 0.25
    x = np.arange(n_groups)

    for i, strat in enumerate(STRATEGIES):
        vals = []
        for aid in asset_ids:
            sub = df[(df["asset_id"] == aid) & (df["strategy"] == strat)]
            vals.append(sub[metric].values[0] if len(sub) > 0 else 0)
        if len(vals) == n_groups:
            offset = (i - n_strats / 2 + 0.5) * bar_width
            bars = ax.bar(x + offset, vals, bar_width,
                          label=strat.replace("_", " ").title(),
                          color=STRATEGY_COLORS.get(strat, None), alpha=0.85)
            # Add value labels
            for bar, val in zip(bars, vals):
                if abs(val) > 0.1:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                            f"{val:.1f}", ha="center", va="bottom", fontsize=6)

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel(ylabel)
    ax.legend(fontsize=7)


def _plot_combined_dashboard(session, asset_ids: list[str], bt_results: dict):
    """Panel 5: Executive summary dashboard."""
    fig = plt.figure(figsize=(20, 14))
    fig.suptitle("Stock Dashboard — Backend E2E Pipeline Verification",
                 fontsize=16, fontweight="bold", y=0.98)

    # Layout: 3 rows
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3,
                          top=0.93, bottom=0.05, left=0.06, right=0.97)

    # Row 1: Price + Drawdown + Correlation mini
    ax_price = fig.add_subplot(gs[0, :2])
    ax_dd = fig.add_subplot(gs[0, 2])

    # Row 2: Best strategy equity curves
    ax_eq1 = fig.add_subplot(gs[1, 0])
    ax_eq2 = fig.add_subplot(gs[1, 1])
    ax_eq3 = fig.add_subplot(gs[1, 2])

    # Row 3: Metrics table + signals heatmap
    ax_table = fig.add_subplot(gs[2, :2])
    ax_signals = fig.add_subplot(gs[2, 2])

    # ── Price chart ──
    price_data = _load_prices_df(session, asset_ids)
    for aid in asset_ids:
        if aid not in price_data:
            continue
        df = price_data[aid]
        norm = df["close"] / df["close"].iloc[0] * 100
        label = ASSET_LABELS.get(aid, aid)
        ax_price.plot(norm.index, norm.values, label=label,
                      color=COLORS.get(aid, None), linewidth=1.0, alpha=0.85)
    ax_price.axhline(y=100, color="gray", linestyle="--", alpha=0.4)
    ax_price.set_title("Normalized Prices (Base=100)")
    ax_price.legend(loc="upper left", fontsize=7, ncol=4)
    ax_price.xaxis.set_major_formatter(mdates.DateFormatter("%y-%m"))

    # ── Drawdown chart (best performing asset per strategy) ──
    ax_dd.set_title("Drawdown (All Strategies)")
    for strat in STRATEGIES:
        for aid in asset_ids:
            if aid in bt_results and strat in bt_results[aid]:
                bt = bt_results[aid][strat]["backtest"]
                eq = bt.equity_curve
                if not eq.empty:
                    dates = pd.to_datetime(eq["date"])
                    ax_dd.fill_between(dates, eq["drawdown"] * 100, 0,
                                       alpha=0.15, color=STRATEGY_COLORS.get(strat))
                break  # Just one asset per strategy for readability
    ax_dd.set_ylabel("Drawdown (%)")
    ax_dd.xaxis.set_major_formatter(mdates.DateFormatter("%y-%m"))

    # ── Equity curves (one per strategy) ──
    eq_axes = [ax_eq1, ax_eq2, ax_eq3]
    for idx, strat in enumerate(STRATEGIES):
        ax = eq_axes[idx]
        ax.set_title(f"{strat.replace('_', ' ').title()} Strategy")
        for aid in asset_ids:
            if aid in bt_results and strat in bt_results[aid]:
                bt = bt_results[aid][strat]["backtest"]
                eq = bt.equity_curve
                if eq.empty:
                    continue
                dates = pd.to_datetime(eq["date"])
                label = ASSET_LABELS.get(aid, aid)
                ax.plot(dates, eq["equity"] / 1e6, label=label,
                        color=COLORS.get(aid), linewidth=0.9, alpha=0.8)
        ax.axhline(y=10, color="gray", linestyle="--", alpha=0.3, linewidth=0.7)
        ax.set_ylabel("Equity (M KRW)")
        ax.legend(fontsize=6, ncol=2)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%y-%m"))

    # ── Metrics summary table ──
    ax_table.axis("off")
    ax_table.set_title("Performance Metrics Summary", fontsize=11, fontweight="bold")

    table_data = []
    col_labels = ["Asset", "Strategy", "CAGR", "MDD", "Sharpe", "Sortino",
                  "Win%", "Trades", "vs B&H"]

    for aid in asset_ids:
        if aid not in bt_results:
            continue
        for strat in STRATEGIES:
            if strat not in bt_results[aid]:
                continue
            m = bt_results[aid][strat]["metrics"]
            table_data.append([
                ASSET_LABELS.get(aid, aid),
                strat.replace("_", " ").title()[:8],
                f"{m.cagr:+.1%}",
                f"{m.mdd:.1%}",
                f"{m.sharpe:.2f}",
                f"{m.sortino:.2f}",
                f"{m.win_rate:.0%}",
                str(m.num_trades),
                f"{(m.excess_return or 0):+.1%}",
            ])

    if table_data:
        table = ax_table.table(
            cellText=table_data,
            colLabels=col_labels,
            loc="center",
            cellLoc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(7)
        table.scale(1, 1.3)

        # Color cells based on values
        for i, row in enumerate(table_data):
            # CAGR color
            cagr_val = float(row[2].strip("%+")) / 100
            cell = table[i + 1, 2]
            cell.set_facecolor("#d4edda" if cagr_val > 0 else "#f8d7da")
            # Sharpe color
            sharpe_val = float(row[4])
            cell = table[i + 1, 4]
            if sharpe_val > 1:
                cell.set_facecolor("#d4edda")
            elif sharpe_val < 0:
                cell.set_facecolor("#f8d7da")

        # Header styling
        for j in range(len(col_labels)):
            table[0, j].set_facecolor("#343a40")
            table[0, j].set_text_props(color="white", fontweight="bold")

    # ── Signal heatmap (latest signals) ──
    ax_signals.set_title("Latest Signals")
    sig_matrix = []
    sig_labels_y = []
    for aid in asset_ids:
        row = []
        for strat in STRATEGIES:
            latest = (
                session.query(SignalDaily)
                .filter(SignalDaily.asset_id == aid, SignalDaily.strategy_id == strat)
                .order_by(SignalDaily.date.desc())
                .first()
            )
            row.append(latest.signal if latest else 0)
        sig_matrix.append(row)
        sig_labels_y.append(ASSET_LABELS.get(aid, aid))

    sig_arr = np.array(sig_matrix)
    ax_signals.imshow(sig_arr, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
    ax_signals.set_xticks(range(len(STRATEGIES)))
    ax_signals.set_xticklabels([s.replace("_", "\n").title()[:10] for s in STRATEGIES], fontsize=7)
    ax_signals.set_yticks(range(len(sig_labels_y)))
    ax_signals.set_yticklabels(sig_labels_y, fontsize=7)

    for i in range(len(sig_labels_y)):
        for j in range(len(STRATEGIES)):
            val = sig_arr[i, j]
            text = {1: "LONG", 0: "FLAT", -1: "SHORT"}.get(val, "?")
            color = "white" if abs(val) == 1 else "black"
            ax_signals.text(j, i, text, ha="center", va="center",
                           fontsize=8, fontweight="bold", color=color)

    fig.savefig(OUTPUT_DIR / "5_combined_dashboard.png", bbox_inches="tight")
    plt.close(fig)
    print("  [5/5] Combined dashboard saved")


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────
def main():
    setup_logging("INFO")

    if SessionLocal is None:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)

    session = SessionLocal()
    t_total = time.perf_counter()

    try:
        # Step 1: DB check
        db_info = check_db(session)
        asset_ids = db_info["asset_ids"]

        # Step 2: Collect latest data
        collect_data(session, asset_ids)

        # Step 3: Generate factors
        generate_factors(session, asset_ids)

        # Step 4: Generate signals
        signal_results, valid_ids = generate_signals(session, asset_ids)

        # Step 5: Run backtests (only for assets that passed preprocessing)
        bt_results = run_backtests(session, valid_ids)

        # Step 6: Visualize
        visualize_all(session, asset_ids, bt_results)

    finally:
        session.close()

    elapsed = time.perf_counter() - t_total

    banner(f"E2E PIPELINE COMPLETE ({elapsed:.1f}s)")
    print(f"  Output: {OUTPUT_DIR}")
    print("  Charts: 5 visualization files generated")
    print("  Ready for Phase 5 (Frontend) development!")


if __name__ == "__main__":
    main()
