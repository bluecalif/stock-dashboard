# P4-5 Agentic Tool 정리 Verification

> Date: 2026-05-10

---

## G5.1 — simulation_replay tool 직접 호출 테스트

**명령**:
```python
from api.services.llm.simulation_tools import simulation_replay
result = simulation_replay.invoke({'asset_code': 'QQQ', 'monthly_amount': 1000000, 'period_years': 10})
```

**Raw output**:
```
asset_code: QQQ
final_asset_krw: 464625183.67
total_return: 2.8399
annualized_return: 0.144
yearly_worst_mdd: -0.2624
```

**검증 결과**: ✅ PASS — `total_return: 2.8399` ≈ Phase 2 fixture 2.84 (±5% 기준 통과)

---

## 변경 내용

| 파일 | 변경 |
|------|------|
| `backend/api/services/llm/simulation_tools.py` | 신규 — simulation_replay/strategy/portfolio 3종 tool |
| `backend/api/services/llm/agentic/data_fetcher.py` | `list_backtests`/`backtest_strategy` 제거, simulation_* 3종 등록 |

**_TOOL_MAP 변경 요약**:
- 제거: `list_backtests`, `backtest_strategy`
- 추가: `simulation_replay`, `simulation_strategy`, `simulation_portfolio`

**설계 원칙 (A-004)**: simulation_tools.py는 HTTP 경유 없이 `simulation_service`를 직접 import하여 호출.
프론트 `/v1/silver/simulate/*`와 동일한 서비스 레이어 사용.

---

## G5.2, G5.3 — Chat smoke test

> Chat API (`/v1/chat/stream`) smoke test는 P4-6 prod 배포 후 진행 (classifier가 simulation_* tool을 선택하는지 확인 필요).
> G5.2/G5.3 evidence는 step-6-cutover.md에 포함.
