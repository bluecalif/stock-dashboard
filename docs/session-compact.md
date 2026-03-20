# Session Compact

> Generated: 2026-03-20 22:35
> Source: Conversation compaction via /compact-and-go

## Goal
그룹 D E2E 디버깅 — `analyze_indicators` → Reporter → 브라우저 전체 플로우에서 "성공률 산출 불가" 버그의 근본 원인 추적. 4개 어젠다 기반 체계적 디버깅.

## Completed
- [x] **디버그 로깅 추가 (4개 파일)**
  - `reporter.py`: system_prompt, user_msg, raw response DEBUG 로그 3개
  - `data_fetcher.py`: indicator_accuracy 키 존재 INFO 로그 1개
  - `chat_service.py`: agentic flow 진입 INFO 로그 1개
  - `main.py`: `logging.basicConfig()` + `LOG_LEVEL` 환경변수 추가
- [x] **어젠다 4: server multiplication** — 중복 서버(3개 PID) 정리, 단일 서버 재시작
- [x] **어젠다 3: bash server log check** — 루트 로거 미설정 발견 및 수정
- [x] **어젠다 2: logging addition issue** — 5개 로그 전부 정상 출력 확인
- [x] **어젠다 1: accuracy call issue** — E2E 플로우 정상 동작 확인 (MACD 73.91%)
- [x] **E2E 디버깅 리포트 작성** — `dev/active/phaseG-context/e2e-debug-report.md`

## Current State

### Git 상태
- 최신 커밋: `d834c97` (master) — analyze_indicators indicator-based 성공률 추가
- 미커밋 변경: 디버그 로깅 추가 (4개 파일) + e2e-debug-report.md

### Changed Files (이번 세션)
- `backend/api/main.py` — `logging.basicConfig()` + `LOG_LEVEL` 환경변수 추가 (버그 수정)
- `backend/api/services/llm/agentic/reporter.py` — DEBUG 로그 3개 추가
- `backend/api/services/llm/agentic/data_fetcher.py` — indicator_accuracy INFO 로그 1개 추가
- `backend/api/services/chat/chat_service.py` — agentic flow 진입 INFO 로그 1개 추가
- `dev/active/phaseG-context/e2e-debug-report.md` — E2E 디버깅 전체 리포트 (신규)

### 서버 상태
- uvicorn PID 22880 (reloader) + PID 21060 (worker) on :8000 실행 중
- 프론트엔드 :5174 실행 중
- `/tmp/uvicorn_e2e.log`에 로그 출력 중

## Remaining / TODO
- [ ] **`signal_accuracy` 용어 모호성 해결** (아래 상세)
- [ ] 이번 세션 디버그 로깅 변경 커밋 여부 결정
- [ ] 디버그 로그를 프로덕션에서 유지할지 결정 (현재 DEBUG 레벨이므로 기본 실행 시 안 보임)
- [ ] Reporter LLM 응답 시간 ~22초 성능 최적화 검토
- [ ] `git push` 후 프로덕션 배포 테스트
- [ ] G-2 대화 요약 검증: 5턴 이상 채팅 후 conversation_summaries 테이블에 요약 저장 확인
- [ ] G-3 Context-Aware 검증: beginner vs expert 응답 톤/깊이 차이 확인

### signal_accuracy 모호성 이슈
`signal_accuracy`라는 개념이 페이지에 따라 의미가 달라지는 문제:

| 페이지 | 의미 | 데이터 소스 | 현재 상태 |
|--------|------|------------|-----------|
| **지표/시그널** (indicators) | RSI/MACD 개별 지표의 매수/매도 성공률 | `indicator_accuracy` (rsi_14, macd) | ✅ d834c97에서 추가, 정상 동작 |
| **전략** (strategy) | momentum/trend/mean_reversion 전략의 성공률 | `signal_accuracy` (strategy 기반) | ⚠️ 데이터 0건, insufficient_data=true |

**현재 문제점**:
1. Classifier가 "MACD 성공률"을 `category=signal_accuracy`로 분류 → 이름이 전략 기반처럼 보이지만 실제로는 indicator 성공률을 원함
2. `analyze_indicators` 툴이 `indicator_accuracy`와 `signal_accuracy`를 **동시에** 반환 → LLM이 어느 것을 참조할지 knowledge_prompt에 의존
3. 전략 페이지에서 "전략 성공률"을 물으면 `signal_accuracy`(모두 insufficient_data)만 참조해야 하는데, `indicator_accuracy`와 혼동 가능

**검토 필요 사항**:
- Classifier의 카테고리 이름을 `indicator_accuracy` vs `strategy_accuracy`로 분리할지
- 페이지 컨텍스트에 따라 반환 데이터를 필터링할지
- 또는 knowledge_prompt 가이드만으로 충분한지 (현재 방식)

## Key Decisions
- **루트 로거 수정**: `main.py`에 `logging.basicConfig(level=LOG_LEVEL)` 추가 — uvicorn `--log-level`은 앱 로거에 영향 없음
- **디버그 로그 레벨**: 새 로그는 DEBUG (상세 데이터), 기존 INFO 유지 — 프로덕션에서 기본적으로 안 보임
- **이전 버그 근본 원인 확정**: `analyze_indicators`에 `indicator_accuracy` 필드 자체가 없었음 → LLM이 `signal_accuracy`(전략 기반, 데이터 0건)만 참조 → d834c97에서 수정 완료

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **E2E 플로우 타임라인** (로그 기반 확인 완료):
  ```
  Classifier(2s) → DataFetcher(8s) → Reporter system/user msg 구성(1s) → LLM 호출(22s) → 응답
  ```
- **핵심 파일**:
  - `backend/api/main.py` (line 30~35) — logging.basicConfig 설정
  - `backend/api/services/llm/agentic/reporter.py` (line 56~57, 77) — 디버그 로그
  - `backend/api/services/llm/agentic/data_fetcher.py` (line 71~75) — indicator_accuracy 로그
  - `dev/active/phaseG-context/e2e-debug-report.md` — 전체 디버깅 리포트
- **서버 관리 교훈**: 서버 시작 전 반드시 `netstat -ano | grep :8000` 확인. 중복 서버 시 로그가 다른 프로세스로 갈 수 있음.
- **유저 지시**: "though there are several issue remained, let me give you the instruction in the next session" — 다음 세션에서 유저가 구체적 지시를 줄 예정

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
1. **signal_accuracy 모호성 해결** — 페이지별 의미 분리 방향 결정
2. 디버그 로깅 커밋, Reporter 성능 최적화, G-2/G-3 검증, 프로덕션 배포
