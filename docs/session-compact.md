# Session Compact

> Generated: 2026-03-21 23:45
> Source: Reporter 성능 최적화 세션

## Goal
Reporter LLM 응답 시간 최적화 (E2E 32초 → 12~15초 목표)

## Completed

### 성능 최적화 구현 (Phase 1~5)
- [x] **Phase 1: Tool Result 압축기** — `compressor.py` 신규 생성. 80%+ 토큰 감소
- [x] **Phase 2: DataFetcher 병렬 실행** — `asyncio.gather` + `run_in_executor`
- [x] **Phase 3: Reporter 파라미터 튜닝** — temperature=0 (원래 0.3)
- [x] **Phase 4: Tool Result 캐싱** — `tool_cache.py` 인메모리 당일 캐시
- [x] **Phase 5: E2E 타이밍 로그** — chat_service.py perf_counter 기반
- [x] **압축기 테스트** — test_compressor.py 13건 추가

### CORS 수정
- [x] **CORS allow_origin_regex 적용** — Vite 동적 포트 할당 문제 근본 해결

### Reporter 타임아웃 근본 원인 해결
- [x] **근본 원인 진단** — gpt-5-mini가 reasoning 모델임을 발견. `temperature=0` → 400 에러 → langchain 자동 재시도로 25s+ 소요
- [x] **모델 벤치마크** — gpt-5-mini(34.8s), gpt-5-nano(36.9s), gpt-4.1-mini(4.5s), gpt-4o-mini(4.9s) 실측
- [x] **Reporter 모델 분리** — `llm_report_model=gpt-4.1-mini` 설정 추가. 34.8s → 5.8s (6배 개선)
- [x] **Classifier 호환성** — temperature 제거, timeout=30s, retries=2, max_completion_tokens=1000
- [x] **Summarizer 호환성** — gpt-5-nano도 reasoning 모델 → temperature=0 제거
- [x] **graph.py 조정** — timeout=60s, retries=2
- [x] **테스트 수정** — reporter 모델 분기 테스트 → 단일 모델 테스트. 874 passed

### 메모리/규칙 저장
- [x] **진단 규칙 추가** — CLAUDE.md + memory

## Current State

### E2E 성능 (실측)
| 시나리오 | Classifier | Fetch | Reporter | Total |
|----------|-----------|-------|----------|-------|
| Cold | 8s | 12s | 5.8s | **~26s** |
| Warm (캐시) | 8s | 1.3s | 5.8s | **~15s** |

### Git 상태
- 최신 커밋: `b7bcb17` (master) — 변경사항 미커밋
- master가 origin보다 4 commits ahead

### 변경된 파일
- `backend/config/settings.py` — `llm_report_model` 추가
- `backend/api/services/llm/agentic/compressor.py` — **신규**
- `backend/api/services/llm/agentic/tool_cache.py` — **신규**
- `backend/api/services/llm/agentic/reporter.py` — gpt-4.1-mini + temperature=0
- `backend/api/services/llm/agentic/classifier.py` — reasoning 모델 호환
- `backend/api/services/llm/agentic/data_fetcher.py` — 병렬 + 캐싱
- `backend/api/services/llm/graph.py` — timeout/retries 조정
- `backend/api/services/chat/chat_service.py` — 타이밍 로그
- `backend/api/services/chat/summarizer.py` — gpt-5-nano 호환
- `backend/api/main.py` — CORS allow_origin_regex
- `backend/.env.example` — LLM_REPORT_MODEL
- `backend/tests/unit/test_agentic_reporter.py` — 모델 테스트 수정
- `backend/tests/unit/test_api/test_compressor.py` — **신규** 13건

### 서버 상태
- Backend: uvicorn --reload 실행 중 (PID 16372, 5336)
- Frontend: npm run dev 실행 중

## Remaining / TODO

### 즉시 필요
- [ ] **E2E 브라우저 테스트**: 사용자가 현재 진행 중
- [ ] **커밋**: 모든 변경사항 커밋 (최적화 + CORS + 모델 분리 + 테스트)
- [ ] **진단 스크립트 정리**: tests/diag_*.py 3개 삭제 (일회용)

### 후순위
- [ ] 프로덕션 배포 테스트
- [ ] DataFetcher cold 최적화 (12s → 목표 미정)

## Key Decisions
- **Reporter 모델 분리**: reasoning 모델(gpt-5-mini) → non-reasoning(gpt-4.1-mini). JSON 리포트 생성에 reasoning 불필요
- **Classifier는 reasoning 유지**: 질문 의도 파악에 chain-of-thought 유효
- **CORS**: `allow_origin_regex` 방식으로 근본 해결
- **압축기 적용 위치**: reporter.py 내부에서 compress_tool_results() 실행

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **테스트**: 874 passed (기존 862 + 신규 13 - 병합 1)
- **진단 규칙**: 에러 발생 시 외부 원인 단정 금지. 모델 호환성(reasoning/non-reasoning) 먼저 확인
- **서버 관리**: Windows uvicorn --reload 불안정. taskkill로 전체 종료 후 재시작
