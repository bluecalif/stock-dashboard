"""Hybrid response templates — hardcoded f-string templates per category.

Each template function returns (text_response, list[UIAction]).
"""

from __future__ import annotations

from .actions import UIAction, highlight_pair, set_filter
from .classifier import (
    CORRELATION_EXPLAIN,
    INDICATOR_COMPARE,
    INDICATOR_EXPLAIN,
    INDICATOR_ACCURACY,
    SIMILAR_ASSETS,
    SPREAD_ANALYSIS,
    STRATEGY_BACKTEST,
    STRATEGY_COMPARE,
    STRATEGY_EXPLAIN,
)
from .context import PageContext

# ---------------------------------------------------------------------------
# Template functions: (PageContext, data) → (str, list[UIAction])
# ---------------------------------------------------------------------------

def _correlation_explain_template(
    ctx: PageContext,
    data: dict,
) -> tuple[str, list[UIAction]]:
    """상관도 설명 템플릿."""
    groups = data.get("groups", [])
    top_pairs = data.get("top_pairs", [])
    nm = data.get("name_map", {})
    dn = lambda x: nm.get(x, x)  # noqa: E731
    period = data.get("period", {})

    lines = ["## 상관도 분석 결과\n"]

    if period:
        lines.append(
            f"분석 기간: {period.get('start', '?')} ~ {period.get('end', '?')} "
            f"({period.get('window', '?')}거래일)\n"
        )

    if groups:
        lines.append("### 함께 움직이는 자산 그룹")
        for g in groups:
            names = ", ".join(dn(a) for a in g["asset_ids"])
            avg = g["avg_correlation"]
            lines.append(
                f"- **그룹 {g['group_id']}**: {names} "
                f"(평균 {avg:.2f} — {g['interpretation']})"
            )
            if avg >= 0.8:
                lines.append(
                    "  - 이 자산들은 매우 유사하게 움직여 "
                    "분산 효과가 제한적입니다."
                )
        lines.append("")

    if top_pairs:
        lines.append("### 상관도 높은 쌍 TOP-5")
        lines.append(
            "상관계수가 높을수록 두 자산이 같은 방향으로 움직입니다.\n"
        )
        for p in top_pairs[:5]:
            corr = p["correlation"]
            lines.append(
                f"- **{dn(p['asset_a'])} ↔ {dn(p['asset_b'])}**: "
                f"{corr:.2f} ({p['interpretation']})"
            )
        lines.append(
            "\n> 히트맵 셀을 클릭하면 두 자산의 스프레드를 상세 분석할 수 있습니다."
        )

    actions: list[UIAction] = []
    if top_pairs:
        top = top_pairs[0]
        actions.append(highlight_pair(top["asset_a"], top["asset_b"]))

    return "\n".join(lines), actions


def _similar_assets_template(
    ctx: PageContext,
    data: dict,
) -> tuple[str, list[UIAction]]:
    """유사자산 추천 템플릿."""
    similar = data.get("similar", [])
    target = data.get("target_id", "")
    nm = data.get("name_map", {})
    dn = lambda x: nm.get(x, x)  # noqa: E731

    lines = [f"## {dn(target)}와 유사한 자산\n"]

    if similar:
        lines.append(
            f"{dn(target)}과(와) 수익률이 비슷하게 움직이는 자산을 "
            f"상관계수 기준으로 정리했습니다.\n"
        )
        for i, s in enumerate(similar, 1):
            corr = s["correlation"]
            aid = s["asset_id"]
            desc = ""
            if corr >= 0.8:
                desc = " — 거의 같은 방향으로 움직입니다"
            elif corr >= 0.5:
                desc = " — 대체로 같은 방향이지만 차이도 있습니다"
            elif corr >= 0:
                desc = " — 약한 양의 관계입니다"
            else:
                desc = " — 반대 방향으로 움직이는 경향이 있습니다"
            lines.append(
                f"{i}. **{dn(aid)}** — "
                f"상관계수 {corr:.2f} ({s['interpretation']}){desc}"
            )
        lines.append(
            f"\n> 히트맵에서 {dn(target)} 행을 확인하면 "
            f"다른 자산과의 상관계수를 한눈에 볼 수 있습니다."
        )
    else:
        lines.append("유사자산 정보를 찾을 수 없습니다.")

    actions: list[UIAction] = []
    if similar and target:
        actions.append(highlight_pair(target, similar[0]["asset_id"]))

    return "\n".join(lines), actions


def _spread_analysis_template(
    ctx: PageContext,
    data: dict,
) -> tuple[str, list[UIAction]]:
    """스프레드 분석 템플릿."""
    asset_a = data.get("asset_a", "?")
    asset_b = data.get("asset_b", "?")
    nm = data.get("name_map", {})
    dn = lambda x: nm.get(x, x)  # noqa: E731
    z = data.get("current_z_score", 0)
    z_interp = data.get("z_score_interpretation", "")
    z_desc = data.get("z_score_description", "")
    events = data.get("convergence_events", [])
    data_points = data.get("data_points", 0)

    lines = [
        f"## {dn(asset_a)} ↔ {dn(asset_b)} 스프레드 분석\n",
        f"두 자산 간 가격 비율의 평균 이탈 정도를 Z-Score로 나타냅니다. "
        f"(데이터: {data_points}거래일)\n",
        f"**현재 Z-Score**: {z:.2f} — {z_interp}",
        f"> {z_desc}\n",
    ]

    if events:
        recent = events[-5:]
        conv_count = sum(1 for e in recent if e["direction"] == "convergence")
        div_count = len(recent) - conv_count
        lines.append(f"### 최근 수렴/발산 이벤트 (수렴 {conv_count}회, 발산 {div_count}회)")
        for e in recent:
            direction = "수렴" if e["direction"] == "convergence" else "발산"
            lines.append(f"- {e['date']}: {direction} (z={e['z_score']:.2f})")

    actions = [highlight_pair(asset_a, asset_b)]
    return "\n".join(lines), actions


# ---------------------------------------------------------------------------
# Indicator templates (D.6)
# ---------------------------------------------------------------------------

_SIGNAL_MAP = {"buy": "매수", "sell": "매도", "neutral": "중립"}
_INDICATOR_DISPLAY = {
    "rsi_14": "RSI (14일)",
    "macd": "MACD",
    "macd_signal": "MACD 시그널",
    "vol_20": "변동성 (20일)",
    "atr_14": "ATR (14일)",
}
_STRATEGY_DISPLAY = {
    "momentum": "모멘텀 (MACD)",
    "trend": "추세 (SMA)",
    "mean_reversion": "평균회귀 (RSI)",
}


def _indicator_explain_template(
    ctx: PageContext,
    data: dict,
) -> tuple[str, list[UIAction]]:
    """현재 지표 상태 해석 템플릿."""
    states = data.get("indicator_states", [])
    asset_id = data.get("asset_id", "?")
    nm = data.get("name_map", {})
    dn = lambda x: nm.get(x, x)  # noqa: E731

    lines = [f"## {dn(asset_id)} 지표 현황\n"]

    if not states:
        lines.append("조회 가능한 지표 데이터가 없습니다.")
    else:
        for s in states:
            signal_kr = _SIGNAL_MAP.get(s["signal"], s["signal"])
            lines.append(
                f"### {s['factor']}  →  **{s['label']}** ({signal_kr})"
            )
            lines.append(f"- 현재 값: {s['value']}")
            lines.append(f"- {s['description']}\n")

    actions: list[UIAction] = []
    if states:
        actions.append(set_filter("factor_name", states[0]["factor"]))
    return "\n".join(lines), actions


def _indicator_accuracy_template(
    ctx: PageContext,
    data: dict,
) -> tuple[str, list[UIAction]]:
    """지표별 매수/매도 성공률 템플릿."""
    results = data.get("indicator_accuracy", [])
    asset_id = data.get("asset_id", "?")
    forward_days = data.get("forward_days", 5)
    nm = data.get("name_map", {})
    dn = lambda x: nm.get(x, x)  # noqa: E731

    lines = [
        f"## {dn(asset_id)} 지표 성공률\n",
        f"신호 발생 후 **{forward_days}거래일** 뒤 수익률 기준입니다.\n",
    ]

    for r in results:
        name = _INDICATOR_DISPLAY.get(r["indicator_id"], r["indicator_id"])
        if r["insufficient_data"]:
            lines.append(f"### {name}\n- 데이터 부족 (신호 {r['evaluated_signals']}개)\n")
            continue

        lines.append(f"### {name}")
        if r["buy_success_rate"] is not None:
            pct = r["buy_success_rate"] * 100
            avg = (r["avg_return_after_buy"] or 0) * 100
            lines.append(f"- 매수 성공률: **{pct:.1f}%** (평균 수익 {avg:+.2f}%)")
        if r["sell_success_rate"] is not None:
            pct = r["sell_success_rate"] * 100
            avg = (r["avg_return_after_sell"] or 0) * 100
            lines.append(f"- 매도 성공률: **{pct:.1f}%** (평균 수익 {avg:+.2f}%)")
        lines.append(f"- 평가 신호: {r['evaluated_signals']}개\n")

    lines.append(
        "> 성공률 60% 이상은 통계적으로 유의미한 예측력입니다."
    )

    return "\n".join(lines), []


def _indicator_compare_template(
    ctx: PageContext,
    data: dict,
) -> tuple[str, list[UIAction]]:
    """전략 예측력 비교 템플릿."""
    ranking = data.get("strategy_ranking", [])
    asset_id = data.get("asset_id", "?")
    forward_days = data.get("forward_days", 5)
    nm = data.get("name_map", {})
    dn = lambda x: nm.get(x, x)  # noqa: E731

    lines = [
        f"## {dn(asset_id)} 전략 예측력 순위\n",
        f"**{forward_days}거래일** 후 수익률 기준 성공률 비교입니다.\n",
        "| 순위 | 전략 | 매수 성공률 | 매도 성공률 | 비고 |",
        "|:----:|------|:----------:|:----------:|------|",
    ]

    for r in ranking:
        name = _STRATEGY_DISPLAY.get(r["strategy_id"], r["strategy_id"])
        rank = r["rank"]
        if r["insufficient_data"]:
            lines.append(f"| {rank} | {name} | - | - | 데이터 부족 |")
        else:
            buy_rate = r["buy_success_rate"]
            sell_rate = r["sell_success_rate"]
            buy = f"{buy_rate * 100:.1f}%" if buy_rate is not None else "-"
            sell = f"{sell_rate * 100:.1f}%" if sell_rate is not None else "-"
            medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else "")
            lines.append(f"| {rank} | {name} | {buy} | {sell} | {medal} |")

    top = next((r for r in ranking if not r["insufficient_data"]), None)
    if top:
        name = _STRATEGY_DISPLAY.get(top["strategy_id"], top["strategy_id"])
        lines.append(f"\n> **{name}** 전략이 가장 높은 예측력을 보여주고 있습니다.")

    return "\n".join(lines), []


# ---------------------------------------------------------------------------
# Strategy templates (E.5)
# ---------------------------------------------------------------------------

_STRATEGY_DISPLAY_E = {
    "momentum": "모멘텀 (MACD)",
    "contrarian": "역발상 (RSI)",
    "risk_aversion": "위험회피 (ATR+변동성)",
}


def _strategy_explain_template(
    ctx: PageContext,
    data: dict,
) -> tuple[str, list[UIAction]]:
    """전략 설명 템플릿."""
    strategy_name = data.get("strategy_name", "")

    explanations = {
        "momentum": (
            "## 모멘텀 전략 (MACD)\n\n"
            "MACD 시그널 라인의 골든크로스/데드크로스를 따라 추세에 올라타는 전략입니다.\n\n"
            "- **매수**: MACD 히스토그램이 양전환 (골든크로스)\n"
            "- **매도**: MACD 히스토그램이 음전환 (데드크로스)\n"
            "- **특징**: 추세가 강한 시장에서 유리, 횡보장에서 손실 가능"
        ),
        "contrarian": (
            "## 역발상 전략 (RSI)\n\n"
            "RSI가 과매도 구간에서 반등을 노리고, 과매수 구간에서 이익을 실현하는 전략입니다.\n\n"
            "- **매수**: RSI 30 이하 (과매도 진입)\n"
            "- **매도**: RSI 70 이상 (과매수 진입) 또는 매수 해제\n"
            "- **특징**: 횡보/반전 시장에서 유리, 강한 추세에서 손실 가능"
        ),
        "risk_aversion": (
            "## 위험회피 전략 (ATR+변동성)\n\n"
            "ATR/가격 비율이나 변동성이 급등하면 시장을 떠나 손실을 줄이는 전략입니다.\n\n"
            "- **기본**: 항상 투자 (Buy & Hold)\n"
            "- **탈출**: ATR/가격 > 3% 또는 변동성 > 30%\n"
            "- **재진입**: 변동성이 정상 수준으로 복귀 시\n"
            "- **특징**: 급락장에서 손실 회피, 상승장에서는 Buy & Hold와 동일"
        ),
    }

    text = explanations.get(
        strategy_name,
        "전략 선택 후 설명을 확인할 수 있습니다.",
    )
    return text, []


def _strategy_backtest_template(
    ctx: PageContext,
    data: dict,
) -> tuple[str, list[UIAction]]:
    """전략 백테스트 결과 요약 템플릿."""
    summary = data.get("summary", "")
    metrics = data.get("metrics", {})
    annual = data.get("annual_performance", [])
    loss_avoided = data.get("loss_avoided")
    strategy_label = data.get("strategy_label", "?")

    lines = [f"## {strategy_label} 백테스트 결과\n"]

    if summary:
        lines.append(f"{summary}\n")

    if metrics:
        tr = metrics.get("total_return", 0)
        cagr = metrics.get("cagr", 0)
        mdd = metrics.get("mdd", 0)
        sharpe = metrics.get("sharpe", 0)
        lines.append("### 성과 지표")
        lines.append(f"- 누적 수익률: **{tr * 100:+.1f}%**")
        lines.append(f"- CAGR: {cagr * 100:+.1f}%")
        lines.append(f"- MDD: {mdd * 100:.1f}%")
        lines.append(f"- Sharpe: {sharpe:.2f}")

        bh = metrics.get("bh_total_return")
        if bh is not None:
            lines.append(f"- Buy & Hold 수익률: {bh * 100:+.1f}%")
        lines.append("")

    if loss_avoided is not None and loss_avoided > 0:
        lines.append(f"### 손실 회피 금액\n- ₩{loss_avoided:,.0f}\n")

    if annual:
        lines.append("### 연간 성과")
        for a in annual:
            fav = "적합" if a.get("is_favorable") else "부적합"
            ret = a.get("return_pct", 0) * 100
            lines.append(
                f"- {a['year']}년: {ret:+.1f}% ({fav}, "
                f"거래 {a.get('num_trades', 0)}회)"
            )

    return "\n".join(lines), []


def _strategy_compare_template(
    ctx: PageContext,
    data: dict,
) -> tuple[str, list[UIAction]]:
    """전략 비교 템플릿."""
    strategies = data.get("strategies", [])

    lines = ["## 전략 비교\n"]

    if not strategies:
        lines.append("비교할 전략 데이터가 없습니다.")
    else:
        lines.append(
            "| 전략 | 수익률 | CAGR | MDD | 거래 수 | 승률 |"
        )
        lines.append("|------|:------:|:----:|:---:|:------:|:----:|")
        for s in strategies:
            name = _STRATEGY_DISPLAY_E.get(s.get("strategy_name", ""), "?")
            m = s.get("metrics", {})
            tr = m.get("total_return", 0) * 100
            cagr = m.get("cagr", 0) * 100
            mdd = m.get("mdd", 0) * 100
            nt = m.get("num_trades", 0)
            wr = m.get("win_rate", 0) * 100
            lines.append(
                f"| {name} | {tr:+.1f}% | {cagr:+.1f}% | "
                f"{mdd:.1f}% | {nt} | {wr:.0f}% |"
            )

    return "\n".join(lines), []


# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------

_TEMPLATE_REGISTRY: dict[str, callable] = {
    CORRELATION_EXPLAIN: _correlation_explain_template,
    SIMILAR_ASSETS: _similar_assets_template,
    SPREAD_ANALYSIS: _spread_analysis_template,
    INDICATOR_EXPLAIN: _indicator_explain_template,
    INDICATOR_ACCURACY: _indicator_accuracy_template,
    INDICATOR_COMPARE: _indicator_compare_template,
    STRATEGY_EXPLAIN: _strategy_explain_template,
    STRATEGY_BACKTEST: _strategy_backtest_template,
    STRATEGY_COMPARE: _strategy_compare_template,
}


def get_template_response(
    category: str,
    ctx: PageContext,
    data: dict,
) -> tuple[str, list[UIAction]] | None:
    """Get a template response for a category.

    Returns (text, actions) if template exists, None otherwise.
    """
    fn = _TEMPLATE_REGISTRY.get(category)
    if fn is None:
        return None
    return fn(ctx, data)


# ---------------------------------------------------------------------------
# Nudge questions — per-page suggestions
# ---------------------------------------------------------------------------

_NUDGE_QUESTIONS: dict[str, list[str]] = {
    "correlation": [
        "어떤 자산들이 비슷하게 움직이나요?",           # → SIMILAR_ASSETS
        "전체 자산의 상관관계를 분석해주세요",           # → CORRELATION_EXPLAIN
        "KOSPI200과 가장 유사한 자산은?",              # → SIMILAR_ASSETS
        "SK하이닉스와 삼성전자의 스프레드를 분석해주세요",  # → SPREAD_ANALYSIS
    ],
    "indicators": [
        "현재 RSI 상태가 궁금해요",
        "지표 성공률을 확인해볼까요?",
        "어떤 전략의 예측력이 가장 높나요?",
    ],
    "strategy": [
        "3개 전략의 수익률을 비교해주세요",
        "최근 1년간 어떤 전략이 가장 좋았나요?",
        "모멘텀 전략의 주요 매매 포인트는?",
    ],
    "prices": [
        "최근 가격 추이를 알려주세요",
        "삼성전자 최근 30일 가격은?",
    ],
    "home": [
        "현재 자산들의 상관관계를 분석해주세요",
        "오늘의 시장 현황을 알려주세요",
    ],
}


def get_nudge_questions(page_id: str) -> list[str]:
    """Get nudge questions for a page."""
    return _NUDGE_QUESTIONS.get(page_id, _NUDGE_QUESTIONS["home"])
