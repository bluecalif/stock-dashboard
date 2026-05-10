# Phase 4 Debug History — 빅뱅 Cut-over
> Gen: silver
> Last Updated: 2026-05-10

버그·디버깅 이력이 발생하면 여기에 추가.

---

## 형식

```markdown
## [날짜] Step P4-N — [버그 제목]

**증상**: ...
**원인**: ...
**수정**: ...
**교훈**: ...
```

---

## [2026-05-10] P4-2~P4-6 — CI 연속 실패 (4회) → 수정 과정

**증상**: P4-1~P4-5 커밋(`3152c2e`) push 후 CI가 4회 연속 실패.

**원인 1 — ruff lint 71개 에러**: CI는 lint 통과 후 배포를 진행하는데(`needs: test`), 기존 코드에 누적된 lint 에러가 lint 단계를 막음. `ruff --fix`를 Windows 로컬에서만 실행하고 CI 환경(Linux)과 수정 결과가 달라 재실패.

**수정 1**: `pyproject.toml`에 `per-file-ignores` 추가 (scripts/tests/alembic/simulation_service 예외). `ruff --fix`를 재실행해 수정된 파일들을 추가 커밋.

**원인 2 — backtest 테스트 실패**: lint 통과 후 `test_backtests.py` (20개 테스트)와 `test_agentic_data_fetcher.py::test_backtest_strategy_args`가 404로 실패. `backtests.py` 라우터 삭제 후 엔드포인트가 없어졌기 때문.

**수정 2**: `test_backtests.py` 전체 삭제, `test_agentic_data_fetcher.py`의 backtest_strategy 테스트를 simulation_replay/strategy 테스트로 교체.

**원인 3 — Silver gen 기준 테스트 불일치**: `test_fdr_client.py::test_symbol_map_completeness`(7→15종), `test_ingest.py`(7→15, 6→14), `test_edge_cases.py` backtest edge case들 실패. Bronze 기준 테스트들이 Silver gen 코드와 충돌.

**수정 3**: Silver gen 기준으로 테스트 수치 수정 + backtest edge case 테스트 제거. CI `2d66c8c` success → Railway+Vercel 배포 완료.

**교훈**:
- CI가 lint에서 막히면 테스트 단계 실패가 숨겨짐 — lint를 먼저 수정해야 테스트 실패가 드러남
- Bronze 기준 테스트들을 Silver gen 시작 시점에 Silver 기준으로 일괄 업데이트했어야 했음
- Windows ruff --fix 결과와 Linux CI ruff 결과가 다를 수 있음 → 로컬에서 확인 후 커밋
