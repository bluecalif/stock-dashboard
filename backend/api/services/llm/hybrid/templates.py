"""Hybrid response templates — hardcoded f-string templates per category.

Each template function returns (text_response, list[UIAction]).
"""

from __future__ import annotations

from .actions import UIAction, highlight_pair, set_filter
from .classifier import (
    CORRELATION_EXPLAIN,
    INDICATOR_COMPARE,
    INDICATOR_EXPLAIN,
    SIGNAL_ACCURACY,
    SIMILAR_ASSETS,
    SPREAD_ANALYSIS,
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


def _signal_accuracy_template(
    ctx: PageContext,
    data: dict,
) -> tuple[str, list[UIAction]]:
    """매수/매도 성공률 템플릿."""
    results = data.get("signal_accuracy", [])
    asset_id = data.get("asset_id", "?")
    forward_days = data.get("forward_days", 5)
    nm = data.get("name_map", {})
    dn = lambda x: nm.get(x, x)  # noqa: E731

    lines = [
        f"## {dn(asset_id)} 매매 신호 성공률\n",
        f"신호 발생 후 **{forward_days}거래일** 뒤 수익률 기준입니다.\n",
    ]

    for r in results:
        name = _STRATEGY_DISPLAY.get(r["strategy_id"], r["strategy_id"])
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
# Template registry
# ---------------------------------------------------------------------------

_TEMPLATE_REGISTRY: dict[str, callable] = {
    CORRELATION_EXPLAIN: _correlation_explain_template,
    SIMILAR_ASSETS: _similar_assets_template,
    SPREAD_ANALYSIS: _spread_analysis_template,
    INDICATOR_EXPLAIN: _indicator_explain_template,
    SIGNAL_ACCURACY: _signal_accuracy_template,
    INDICATOR_COMPARE: _indicator_compare_template,
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
