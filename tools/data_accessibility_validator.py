#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import struct
import time
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REQUIRED = {"Open", "High", "Low", "Close", "Volume"}
TH = {"success_rate_min": 0.99, "fail_rate_max": 0.01, "missing_ratio_max": 0.005, "p95_ms_max": 2000}
FDR = ["KS200", "005930", "000660", "SOXL", "BTC/KRW", "GC=F", "SI=F"]
KIWOOM = ["005930", "000660"]


@dataclass
class Check:
    name: str
    success: bool
    skipped: bool = False
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


def pct(values: List[float], p: float) -> float:
    if not values:
        return math.nan
    values = sorted(values)
    i = max(0, min(len(values) - 1, math.ceil((p / 100) * len(values)) - 1))
    return values[i]


def fetch_fdr(symbol: str, start_date: str, retries: int) -> Tuple[Any, float]:
    import FinanceDataReader as fdr  # type: ignore

    started = time.perf_counter()
    last = None
    for n in range(retries + 1):
        try:
            return fdr.DataReader(symbol, start_date), (time.perf_counter() - started) * 1000
        except Exception as e:  # noqa: BLE001
            last = e
            if n < retries:
                time.sleep(min(2**n, 8))
    raise RuntimeError(f"FDR fetch failed: {symbol}: {last}") from last


def kiwoom_session(mode: str) -> Tuple[Optional[Any], Check]:
    if mode == "skip":
        return None, Check("kiwoom_session", False, skipped=True, error="kiwoom_skipped")
    if platform.system().lower() != "windows":
        err = "kiwoom_non_windows"
        return (None, Check("kiwoom_session", False, skipped=(mode == "auto"), error=err))
    py_bits = struct.calcsize("P") * 8
    if py_bits != 32:
        # KHOpenAPI ActiveX is 32-bit only in practice.
        return (
            None,
            Check(
                "kiwoom_session",
                False,
                skipped=(mode == "auto"),
                error="kiwoom_requires_32bit_python",
                details={"python_bits": py_bits, "python_executable": os.sys.executable},
            ),
        )
    started = time.perf_counter()
    try:
        from pykiwoom.kiwoom import Kiwoom  # type: ignore

        k = Kiwoom()
        k.CommConnect(block=True)
        return k, Check("kiwoom_session", True, latency_ms=(time.perf_counter() - started) * 1000)
    except Exception as e:  # noqa: BLE001
        return None, Check(
            "kiwoom_session",
            False,
            skipped=(mode == "auto"),
            latency_ms=(time.perf_counter() - started) * 1000,
            error=str(e),
        )


def norm_kiwoom(df: Any) -> Any:
    import pandas as pd  # type: ignore

    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    m = {"일자": "Date", "날짜": "Date", "시가": "Open", "고가": "High", "저가": "Low", "현재가": "Close", "종가": "Close", "거래량": "Volume"}
    out = df.rename(columns={k: v for k, v in m.items() if k in df.columns})
    need = ["Date", "Open", "High", "Low", "Close", "Volume"]
    for c in need:
        if c not in out.columns:
            raise RuntimeError(f"kiwoom missing col: {c}; cols={list(out.columns)}")
    for c in ["Open", "High", "Low", "Close", "Volume"]:
        out[c] = out[c].astype(str).str.replace(",", "", regex=False).str.replace("+", "", regex=False).str.strip().astype(float).abs()
    out["Date"] = pd.to_datetime(out["Date"].astype(str), format="%Y%m%d", errors="coerce")
    out = out.dropna(subset=["Date"]).set_index("Date").sort_index()
    out = out[["Open", "High", "Low", "Close", "Volume"]]
    out = out[~out.index.duplicated(keep="first")]
    return out


def fetch_kiwoom(k: Any, code: str, start_date: str, retries: int, max_pages: int) -> Tuple[Any, float]:
    import pandas as pd  # type: ignore

    started = time.perf_counter()
    last = None
    for n in range(retries + 1):
        try:
            args = {"종목코드": code, "기준일자": date.today().strftime("%Y%m%d"), "수정주가구분": 1, "output": "주식일봉차트조회"}
            frames = [norm_kiwoom(k.block_request("opt10081", next=0, **args))]
            pages = 1
            while getattr(k, "tr_remained", False) and pages < max_pages:
                time.sleep(0.35)
                d = norm_kiwoom(k.block_request("opt10081", next=2, **args))
                frames.append(d)
                pages += 1
                if len(d) and d.index.min().date().isoformat() <= start_date:
                    break
            df = pd.concat(frames) if frames else pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
            df = df[~df.index.duplicated(keep="first")].sort_index()
            df = df[df.index >= pd.Timestamp(start_date)]
            return df, (time.perf_counter() - started) * 1000
        except Exception as e:  # noqa: BLE001
            last = e
            if n < retries:
                time.sleep(min(2**n, 8))
    raise RuntimeError(f"Kiwoom fetch failed: {code}: {last}") from last


def check_df(asset_id: str, df: Any) -> Dict[str, Any]:
    r: Dict[str, Any] = {"asset_id": asset_id, "row_count": int(len(df)), "required_ok": False, "dup": 0, "neg": 0, "inv": 0, "missing_ratio": 0.0, "latest_date": None}
    miss = sorted(REQUIRED - set(df.columns))
    r["missing_columns"] = miss
    r["required_ok"] = len(miss) == 0
    if len(df) == 0:
        return r
    r["dup"] = int(df.index.duplicated().sum()) if hasattr(df.index, "duplicated") else 0
    try:
        r["latest_date"] = str(df.index.max().date())
    except Exception:  # noqa: BLE001
        r["latest_date"] = str(df.index.max())
    if r["required_ok"]:
        r["inv"] = int((df["High"] < df["Low"]).sum())
        r["neg"] = int((df[["Open", "High", "Low", "Close"]] < 0).sum().sum())
        miss_cells = df[["Open", "High", "Low", "Close", "Volume"]].isna().sum().sum()
        r["missing_ratio"] = float(miss_cells / (len(df) * 5))
    return r


def add_fetch_checks(kind: str, assets: List[str], fetcher, start_date: str, retries: int, checks: List[Check], suffix: str = "") -> None:
    for a in assets:
        name = f"{kind}:{a}{suffix}"
        started = time.perf_counter()
        try:
            df, lat = fetcher(a, start_date, retries)
            d = check_df(a + suffix, df)
            ok = d["required_ok"] and d["row_count"] > 0
            if kind == "backfill":
                ok = ok and d["dup"] == 0 and d["neg"] == 0 and d["inv"] == 0 and d["missing_ratio"] <= TH["missing_ratio_max"]
            if kind == "freshness":
                lag = None if not d["latest_date"] else (date.today() - date.fromisoformat(d["latest_date"])).days
                d["lag_days"] = lag
                ok = ok and lag is not None and lag <= 3
            checks.append(Check(name, ok, latency_ms=lat, details=d))
        except Exception as e:  # noqa: BLE001
            checks.append(Check(name, False, latency_ms=(time.perf_counter() - started) * 1000, error=str(e)))


def reliability(kind: str, assets: List[str], fetcher, start_date: str, retries: int, repeats: int, checks: List[Check], suffix: str = "") -> None:
    for a in assets:
        lat: List[float] = []
        fail0 = 0
        failr = 0
        for _ in range(repeats):
            try:
                _, t = fetcher(a, start_date, 0)
                lat.append(t)
            except Exception:  # noqa: BLE001
                fail0 += 1
                if repeats > 0 and (fail0 / repeats) > TH["fail_rate_max"]:
                    break
        for _ in range(repeats):
            try:
                fetcher(a, start_date, retries)
            except Exception:  # noqa: BLE001
                failr += 1
                if repeats > 0 and (failr / repeats) > TH["fail_rate_max"]:
                    break
        d = {"asset_id": a + suffix, "repeats": repeats, "fail_no_retry": fail0, "fail_with_retry": failr, "fail_rate_with_retry": (failr / repeats), "p95_ms": pct(lat, 95) if lat else None}
        ok = d["fail_rate_with_retry"] <= TH["fail_rate_max"] and (d["p95_ms"] is None or d["p95_ms"] <= TH["p95_ms_max"])
        checks.append(Check(f"{kind}:{a}{suffix}", ok, details=d))


def summarize(checks: List[Check]) -> Dict[str, Any]:
    total = len(checks)
    ev = [c for c in checks if not c.skipped]
    suc = [c for c in ev if c.success]
    fail_rates = [float(c.details.get("fail_rate_with_retry")) for c in ev if c.name.startswith("reliability:") and c.details and isinstance(c.details.get("fail_rate_with_retry"), (int, float))]
    p95s = [float(c.details.get("p95_ms")) for c in ev if c.name.startswith("reliability:") and c.details and isinstance(c.details.get("p95_ms"), (int, float))]
    critical = 0
    for c in ev:
        if c.name.startswith("backfill:") and c.details:
            if c.details.get("dup", 0) > 0 or c.details.get("neg", 0) > 0 or c.details.get("inv", 0) > 0:
                critical += 1
    sr = len(suc) / len(ev) if ev else 0.0
    mfr = max(fail_rates) if fail_rates else 1.0
    mp95 = max(p95s) if p95s else math.inf
    gate = "Go" if (sr >= TH["success_rate_min"] and mfr <= TH["fail_rate_max"] and mp95 <= TH["p95_ms_max"] and critical == 0) else ("No-Go" if critical > 0 else "Conditional Go")
    return {"total_checks": total, "evaluated_checks": len(ev), "success_checks": len(suc), "skipped_checks": total - len(ev), "success_rate": sr, "max_fail_rate_with_retry": mfr, "max_p95_ms": mp95, "critical_errors": critical, "gate": gate, "thresholds": TH}


def md(report: Dict[str, Any]) -> str:
    g = report["gate_summary"]
    out = ["# Data Accessibility Report", "", f"- generated_at_utc: {report['generated_at_utc']}", f"- gate: **{g['gate']}**", "", "## 1. Summary", f"- total_checks: {g['total_checks']}", f"- evaluated_checks: {g['evaluated_checks']}", f"- success_checks: {g['success_checks']}", f"- skipped_checks: {g['skipped_checks']}", f"- success_rate: {g['success_rate']:.2%}", f"- max_fail_rate_with_retry: {g['max_fail_rate_with_retry']:.2%}", f"- max_p95_ms: {g['max_p95_ms']}", f"- critical_errors: {g['critical_errors']}", "", "## 2. Detailed Checks"]
    for c in report["checks"]:
        st = "SKIP" if c.get("skipped") else ("PASS" if c["success"] else "FAIL")
        out.append(f"### {c['name']} [{st}]")
        if c.get("latency_ms") is not None:
            out.append(f"- latency_ms: {c['latency_ms']:.2f}")
        if c.get("error"):
            out.append(f"- error: `{c['error']}`")
        if c.get("details"):
            out.append("- details:")
            for k, v in c["details"].items():
                out.append(f"  - {k}: {v}")
        out.append("")
    out += ["## 3. Recommendation", "- Start implementation." if g["gate"] == "Go" else ("- Fix critical issues before implementation." if g["gate"] == "No-Go" else "- Conditional start with mitigation plan."), ""]
    return "\n".join(out)


def parse() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Data accessibility validator")
    p.add_argument("--smoke-days", type=int, default=30)
    p.add_argument("--backfill-years", type=int, default=3)
    p.add_argument("--repeats", type=int, default=20)
    p.add_argument("--kiwoom-repeats", type=int, default=5)
    p.add_argument("--retries", type=int, default=2)
    p.add_argument("--kiwoom-max-pages", type=int, default=10)
    p.add_argument("--kiwoom-mode", choices=["auto", "require", "skip"], default="auto")
    p.add_argument("--check-environment", action="store_true")
    p.add_argument("--fail-fast", action="store_true", default=True, help="Stop early when a stage fails")
    p.add_argument("--no-fail-fast", dest="fail_fast", action="store_false", help="Run full checks even after failures")
    p.add_argument("--output-json", default="docs/data-accessibility-report.json")
    p.add_argument("--output-md", default="docs/data-accessibility-report.md")
    return p.parse_args()


def has_failed_eval(checks: List[Check], start_idx: int = 0) -> bool:
    for c in checks[start_idx:]:
        if not c.skipped and not c.success:
            return True
    return False


def write_report(args: argparse.Namespace, checks: List[Check]) -> Dict[str, Any]:
    report = {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "input": vars(args),
        "checks": [asdict(c) for c in checks],
    }
    report["gate_summary"] = summarize(checks)

    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.output_md).write_text(md(report), encoding="utf-8")
    return report


def main() -> None:
    args = parse()
    checks: List[Check] = []
    k, kc = kiwoom_session(args.kiwoom_mode)
    checks.append(kc)
    if args.check_environment:
        db = os.getenv("DATABASE_URL")
        checks.append(Check("postgres_connection", bool(db), error=None if db else "DATABASE_URL_not_set"))

    smoke_from = (date.today() - timedelta(days=args.smoke_days * 2)).isoformat()
    backfill_from = (date.today() - timedelta(days=365 * args.backfill_years)).isoformat()
    fresh_from = (date.today() - timedelta(days=30)).isoformat()

    stage_start = len(checks)
    add_fetch_checks("smoke", FDR, lambda a, s, r: fetch_fdr(a, s, r), smoke_from, args.retries, checks)
    if args.fail_fast and has_failed_eval(checks, stage_start):
        report = write_report(args, checks)
        print(f"[DONE] data accessibility validation complete. gate={report['gate_summary']['gate']}")
        print(f"[DONE] json={args.output_json}")
        print(f"[DONE] markdown={args.output_md}")
        print("[FAIL-FAST] stopped after smoke(FDR)")
        return

    stage_start = len(checks)
    add_fetch_checks("backfill", FDR, lambda a, s, r: fetch_fdr(a, s, r), backfill_from, args.retries, checks)
    if args.fail_fast and has_failed_eval(checks, stage_start):
        report = write_report(args, checks)
        print(f"[DONE] data accessibility validation complete. gate={report['gate_summary']['gate']}")
        print(f"[DONE] json={args.output_json}")
        print(f"[DONE] markdown={args.output_md}")
        print("[FAIL-FAST] stopped after backfill(FDR)")
        return

    stage_start = len(checks)
    reliability("reliability", FDR, lambda a, s, r: fetch_fdr(a, s, r), fresh_from, args.retries, args.repeats, checks)
    if args.fail_fast and has_failed_eval(checks, stage_start):
        report = write_report(args, checks)
        print(f"[DONE] data accessibility validation complete. gate={report['gate_summary']['gate']}")
        print(f"[DONE] json={args.output_json}")
        print(f"[DONE] markdown={args.output_md}")
        print("[FAIL-FAST] stopped after reliability(FDR)")
        return

    stage_start = len(checks)
    add_fetch_checks("freshness", FDR, lambda a, s, r: fetch_fdr(a, s, r), fresh_from, args.retries, checks)
    if args.fail_fast and has_failed_eval(checks, stage_start):
        report = write_report(args, checks)
        print(f"[DONE] data accessibility validation complete. gate={report['gate_summary']['gate']}")
        print(f"[DONE] json={args.output_json}")
        print(f"[DONE] markdown={args.output_md}")
        print("[FAIL-FAST] stopped after freshness(FDR)")
        return

    if k is None:
        for code in KIWOOM:
            checks.append(Check(f"smoke:{code}:kiwoom", False, skipped=True, error="kiwoom_unavailable"))
            checks.append(Check(f"backfill:{code}:kiwoom", False, skipped=True, error="kiwoom_unavailable"))
            checks.append(Check(f"reliability:{code}:kiwoom", False, skipped=True, error="kiwoom_unavailable"))
            checks.append(Check(f"freshness:{code}:kiwoom", False, skipped=True, error="kiwoom_unavailable"))
    else:
        stage_start = len(checks)
        add_fetch_checks("smoke", KIWOOM, lambda a, s, r: fetch_kiwoom(k, a, s, r, args.kiwoom_max_pages), smoke_from, args.retries, checks, ":kiwoom")
        if args.fail_fast and has_failed_eval(checks, stage_start):
            report = write_report(args, checks)
            print(f"[DONE] data accessibility validation complete. gate={report['gate_summary']['gate']}")
            print(f"[DONE] json={args.output_json}")
            print(f"[DONE] markdown={args.output_md}")
            print("[FAIL-FAST] stopped after smoke(Kiwoom)")
            return

        stage_start = len(checks)
        add_fetch_checks("backfill", KIWOOM, lambda a, s, r: fetch_kiwoom(k, a, s, r, args.kiwoom_max_pages), backfill_from, args.retries, checks, ":kiwoom")
        if args.fail_fast and has_failed_eval(checks, stage_start):
            report = write_report(args, checks)
            print(f"[DONE] data accessibility validation complete. gate={report['gate_summary']['gate']}")
            print(f"[DONE] json={args.output_json}")
            print(f"[DONE] markdown={args.output_md}")
            print("[FAIL-FAST] stopped after backfill(Kiwoom)")
            return

        stage_start = len(checks)
        reliability("reliability", KIWOOM, lambda a, s, r: fetch_kiwoom(k, a, s, r, 1), fresh_from, args.retries, args.kiwoom_repeats, checks, ":kiwoom")
        if args.fail_fast and has_failed_eval(checks, stage_start):
            report = write_report(args, checks)
            print(f"[DONE] data accessibility validation complete. gate={report['gate_summary']['gate']}")
            print(f"[DONE] json={args.output_json}")
            print(f"[DONE] markdown={args.output_md}")
            print("[FAIL-FAST] stopped after reliability(Kiwoom)")
            return

        stage_start = len(checks)
        add_fetch_checks("freshness", KIWOOM, lambda a, s, r: fetch_kiwoom(k, a, s, r, args.kiwoom_max_pages), fresh_from, args.retries, checks, ":kiwoom")
        if args.fail_fast and has_failed_eval(checks, stage_start):
            report = write_report(args, checks)
            print(f"[DONE] data accessibility validation complete. gate={report['gate_summary']['gate']}")
            print(f"[DONE] json={args.output_json}")
            print(f"[DONE] markdown={args.output_md}")
            print("[FAIL-FAST] stopped after freshness(Kiwoom)")
            return

        # FDR vs Kiwoom close compare (latest point)
        stage_start = len(checks)
        for code in KIWOOM:
            try:
                df_f, _ = fetch_fdr(code, fresh_from, args.retries)
                df_k, _ = fetch_kiwoom(k, code, fresh_from, args.retries, args.kiwoom_max_pages)
                if len(df_f) and len(df_k):
                    f_close = float(df_f["Close"].iloc[-1])
                    k_close = float(df_k["Close"].iloc[-1])
                    diff = abs(f_close - k_close)
                    ratio = diff / k_close if k_close else math.inf
                    checks.append(Check(f"freshness_compare:fdr_vs_kiwoom:{code}", ratio <= 0.01, details={"fdr_close": f_close, "kiwoom_close": k_close, "abs_diff": diff, "diff_ratio": ratio, "pass_threshold_ratio": 0.01}))
                else:
                    checks.append(Check(f"freshness_compare:fdr_vs_kiwoom:{code}", False, skipped=True, error="compare_data_missing"))
            except Exception as e:  # noqa: BLE001
                checks.append(Check(f"freshness_compare:fdr_vs_kiwoom:{code}", False, error=str(e)))
        if args.fail_fast and has_failed_eval(checks, stage_start):
            report = write_report(args, checks)
            print(f"[DONE] data accessibility validation complete. gate={report['gate_summary']['gate']}")
            print(f"[DONE] json={args.output_json}")
            print(f"[DONE] markdown={args.output_md}")
            print("[FAIL-FAST] stopped after freshness_compare")
            return

    report = write_report(args, checks)

    print(f"[DONE] data accessibility validation complete. gate={report['gate_summary']['gate']}")
    print(f"[DONE] json={args.output_json}")
    print(f"[DONE] markdown={args.output_md}")


if __name__ == "__main__":
    main()
