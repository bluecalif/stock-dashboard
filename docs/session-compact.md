# Session Compact

> Generated: 2026-03-21 (세션 2)
> Source: Conversation compaction via /compact-and-go

## Goal
`signal_accuracy` 용어 모호성 해결 — 전략 기반 dead code 정리 + `indicator_accuracy` 카테고리 명확화.

## Completed
- [x] **signal_accuracy 모호성 해결** (`19c4dcd`)
  - `analyze_indicators` 툴에서 전략 기반 dead 블록 제거 (signal_accuracy, strategy_ranking 필드 삭제, compute_signal_accuracy/compare_indicator_accuracy import 제거)
  - Classifier/Templates/Schemas 카테고리: `signal_accuracy` → `indicator_accuracy`
  - `_signal_accuracy_template` → `_indicator_accuracy_template` (indicator 데이터 참조로 변경)
  - 프론트엔드 dead export 제거 (`fetchSignalAccuracy`, `fetchIndicatorComparison`, `SignalAccuracyByStrategyParams`)
  - `knowledge_prompts.py`: 전략 비교 라우팅 라인 삭제
  - 테스트 업데이트: 858 tests passed, 0 failed
  - 문서 업데이트 + 커밋 + push 완료

## Current State

### Git 상태
- 최신 커밋: `19c4dcd` (master, pushed) — signal_accuracy 모호성 해결
- 미커밋 변경: 없음 (clean working tree, `_context.md`와 `bash.exe.stackdump`만 untracked)

### 변경된 파일 (이번 세션, 9 files, +38/-132)
- `backend/api/services/llm/tools.py` — strategy dead 블록 삭제 + import 정리
- `backend/api/services/llm/hybrid/classifier.py` — SIGNAL_ACCURACY → INDICATOR_ACCURACY
- `backend/api/services/llm/hybrid/templates.py` — _indicator_accuracy_template + _INDICATOR_DISPLAY 매핑 추가
- `backend/api/services/llm/agentic/knowledge_prompts.py` — 카테고리명 + 프롬프트 업데이트
- `backend/api/services/llm/agentic/schemas.py` — Category Literal 업데이트
- `frontend/src/api/analysis.ts` — dead export 3개 삭제
- `backend/tests/unit/test_hybrid_classifier.py` — indicator_accuracy 기반 테스트 데이터
- `backend/tests/unit/test_knowledge_prompts.py` — 카테고리명 업데이트
- `docs/session-compact.md` — TODO 완료 처리

### 유지한 것 (향후 복구 가능)
- `compute_signal_accuracy()`, `compute_accuracy_all_strategies()` 함수
- `compare_indicator_accuracy()` 함수
- `/v1/analysis/signal-accuracy?strategy_id=X` API 엔드포인트
- `signal_daily` 테이블, `SignalDaily` 모델
- 관련 테스트 파일들

## Remaining / TODO

### 성능/배포
- [ ] Reporter LLM 응답 시간 ~22초 성능 최적화 검토
- [ ] 프로덕션 배포 테스트

### 채팅 품질
- [ ] 대시보드-채팅 일치성: 지표/시그널 페이지에서 시그널+성공률 탭 통합 설명 정책 결정
- [ ] 대시보드-채팅 일치성: 종목/기간/시점을 응답에 항상 명시하도록 개선

### 기타
- [ ] 회원 탈퇴 기능 추가
- [ ] 대시보드(홈) 데이터가 현재 기준으로 업데이트 안 되는 문제 수정

### 완료
- [x] G-2 대화 요약 검증: _run_summary DB 세션 버그 수정 → 5턴 후 요약 생성 + top_assets/top_categories 갱신 확인
- [x] G-3 Context-Aware 검증: beginner vs expert 프로필 변경 시 응답 톤/깊이 차이 브라우저 E2E 확인
- [x] 이번 세션 디버그 로깅 변경 커밋 여부 결정 (3af6033에서 이미 커밋됨 확인)
- [x] 채팅 대화 컨텍스트: Classifier+Reporter에 최근 3턴 히스토리 전달 (이전 대화 참조 가능)
- [x] unsupported 질문 라우팅: 거부 메시지 → LangGraph fallback으로 일반 대화 처리

## Key Decisions
- **전략 기반 signal_accuracy 전체가 dead code**: signal_daily 테이블 데이터 0건, run_research 미실행 → tool 출력에서 제거 (서비스/API는 유지)
- **카테고리명 indicator_accuracy로 통일**: 실제 동작하는 것이 지표 성공률뿐이므로 이름을 실체에 맞게 변경
- **_STRATEGY_DISPLAY 유지**: `_indicator_compare_template`에서 여전히 strategy 데이터 표시에 사용하므로 삭제하지 않음

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **프로젝트 상태**: 전 Phase 완료 (MVP~Phase G, 858 tests)
- **E2E 플로우**: Classifier(2s) → DataFetcher(8s) → Reporter(22s) → 응답
- **핵심 참조**: `dev/active/phaseG-context/e2e-debug-report.md` (E2E 디버깅 리포트)

## Project Status

| Phase | 상태 | 비고 |
|-------|------|------|
| MVP (0~7) | ✅ 완료 | 83/83 tasks |
| Phase A Auth | ✅ 완료 | 16/16 tasks |
| Phase B Chatbot | ✅ 완료 | 19/19 tasks |
| Phase C 상관도 | ✅ 완료 | 12/12 Steps |
| Phase C-rev 피드백 | ✅ 완료 | 7/7 Tasks |
| Phase C-rev2 피드백 | ✅ 완료 | 4/4 Tasks |
| Phase D 지표 | ✅ 완료 | 12/12 Tasks |
| Phase D-rev 피드백 | ✅ 완료 | 13/13 Tasks |
| Phase D-improve | ✅ 완료 | 7/7 Tasks |
| Phase E 전략 | ✅ 완료 | 10/10 Tasks |
| Phase F Agentic | ✅ 완료 | 10/10 Tasks |
| Phase G Context | ✅ 완료 | 20/20 tasks |

## Next Action
다음 세션에서 유저의 구체적 지시를 기다린 후 진행. 우선 후보:
1. Reporter 성능 최적화 (~22초 → 목표 10초 이내)
2. G-2/G-3 기능 검증 (대화 요약, 개인화 응답)
3. 프로덕션 배포 테스트
