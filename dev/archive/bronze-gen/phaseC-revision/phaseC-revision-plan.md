# Phase C-rev: 상관도 페이지 피드백 반영
> Last Updated: 2026-03-14
> Status: Planning
> Source: `docs/post-mvp-feedback.md` (프로덕션 브라우저 리뷰)

## 1. Summary (개요)

**목적**: Phase C 완료 후 프로덕션 브라우저 리뷰에서 발견된 7개 이슈 수정
**범위**: 상관도 페이지 UX 개선 + 채팅 UX 개선 + LangSmith 모니터링
**원칙**: Phase D 진입 전 완료 — 기존 Phase C 코드 위에 수정/확장

## 2. Current State (현재 상태)

- Phase C 12/12 Steps 완료, 프로덕션 배포 완료
- 테스트: 561 passed, ruff/tsc/vite clean
- LangSmith `.env` 설정 완료 (LANGCHAIN_TRACING_V2=true)

## 3. Target State (목표 상태)

- 종목 코드(005930) → 종목명(삼성전자) 표시 + 그래프별 설명 텍스트
- 상관계수 분포 차트 제거
- 히트맵 셀 클릭 → Scatter + Spread 연동 (통합 인터랙션)
- 스프레드: 정규화 가격 오버레이 차트 추가 (z-score 하단 유지)
- 채팅: 스트림 시작 전 단계별 상태 표시 UX
- 넛지 질문: 클릭 시 템플릿 응답 (LLM 호출 제거)
- LangSmith 트레이싱 활성화 (완료)

## 4. Implementation Stages

### Stage A: 데이터 기반 — 종목명 매핑 (CR.1)

**CR.1 종목명 매핑 + 그래프 설명** `[M]`

Backend:
- `GET /v1/assets` 응답에 이미 `name` 필드 존재 (asset_master 테이블)
- 상관도 API 응답(`/v1/correlation`, `/v1/correlation/analysis`, `/v1/correlation/spread`)에 `asset_names` 매핑 dict 추가
  - 예: `{"asset_names": {"KS200": "KOSPI200", "005930": "삼성전자", ...}}`
- `correlation.py` 라우터에서 `asset_master` 조회 → 응답에 포함

Frontend:
- `CorrelationPage.tsx`: 페이지 mount 시 `/v1/assets` 호출 → `assetNameMap` 상태 생성
- 히트맵 축 라벨: `assetNameMap[id] || id`로 표시
- 모든 하위 컴포넌트에 `nameMap` prop 전달
- 각 차트 섹션에 subtitle 텍스트 추가:
  - 히트맵: "자산 간 수익률 상관계수 (-1 ~ +1). 색이 진할수록 강한 상관."
  - Scatter Plot: "선택한 두 자산의 일별 수익률 산점도."
  - SpreadChart: "두 자산의 정규화 가격 비교 + 괴리 감지."

### Stage B: 히트맵 인터랙션 통합 (CR.2~CR.3)

**CR.2 상관계수 분포 삭제** `[S]`
- `CorrelationPage.tsx`에서 분포 히스토그램 섹션 제거
- 관련 API 호출/상태 제거 (있다면)

**CR.3 히트맵 셀 클릭 → Scatter + Spread 연동** `[L]`

현재 동작:
- Scatter Plot이 항상 전체 페어로 표시
- 히트맵과 Scatter 간 직접 연동 없음
- Spread는 Scatter 클릭 또는 그룹 카드 클릭으로만 활성화

변경:
- 히트맵 셀 클릭 핸들러 추가 → `chartActionStore.setHighlightedPair(asset_a, asset_b)`
- Scatter Plot: `highlightedPair`가 있으면 해당 점만 강조 (기존 동작 유지)
- Spread: `highlightedPair` 변경 시 자동 로드 (기존 동작 유지)
- **결과**: 히트맵 클릭 → Scatter 강조 + Spread 로드가 하나의 flow로 통합
- 히트맵 대각선(자기자신) 클릭 무시
- 히트맵 셀에 hover 시 커서 pointer + 약한 하이라이트

추가 — 3종목 그룹 페어 선택:
- 그룹 카드 클릭 시 기존: 첫 2종목 자동 선택
- 변경: 그룹 내 3종목이면 드롭다운/라디오로 페어 선택 UI 표시
  - 예: `{삼성전자, SK하이닉스, SOXL}` → "삼성전자↔SK하이닉스", "삼성전자↔SOXL", "SK하이닉스↔SOXL" 중 선택
  - 2종목 그룹은 기존대로 자동 선택
- 또는 히트맵 셀 클릭이 이미 해결하므로, 그룹 카드는 "그룹 내 자산 하이라이트"만 담당하고 페어 선택은 히트맵에 위임 가능
- **결정**: 히트맵 셀 클릭을 primary 페어 선택 수단으로 하고, 그룹 카드 클릭은 히트맵에서 해당 그룹 영역 강조 + 첫 페어 자동 선택

### Stage C: 스프레드 차트 개선 (CR.4)

**CR.4 정규화 가격 오버레이 + Z-score 하단** `[L]`

현재: Z-score 라인차트 + ±1σ/±2σ 밴드만 표시
문제: 실제 가격 갭이 벌어졌다 좁혀지는 모습이 안 보임

Backend 변경:
- `GET /v1/correlation/spread` 응답에 `normalized_prices` 추가
  ```json
  {
    "normalized_prices": {
      "asset_a": [100, 102.3, ...],
      "asset_b": [100, 99.8, ...]
    }
  }
  ```
- `spread_service.py`: `SpreadResult`에 `norm_a_values`, `norm_b_values` 필드 추가
- 정규화 = 첫 날 가격을 100으로 (이미 `norm_a = df["a"] / df["a"].iloc[0]` 계산 중 → `* 100`)
- `correlation.py` 라우터: 응답 스키마에 포함
- `correlation.py` 스키마: `SpreadResponse`에 `normalized_prices` 추가

Frontend 변경 (`SpreadChart.tsx`):
- 2-패널 레이아웃:
  - **상단 (60%)**: 정규화 가격 오버레이 차트
    - 두 종목의 base=100 가격 라인 (서로 다른 색)
    - 갭이 벌어지고 좁혀지는 모습이 시각적으로 보임
    - Y축: 정규화 가격 (100 기준)
    - 범례: 종목명 (nameMap 활용)
  - **하단 (40%)**: Z-score 밴드 차트 (기존 것 축소)
    - ±1σ/±2σ 밴드 유지
    - 수렴/발산 이벤트 태그 유지
- Brush 또는 X축 동기화: 두 차트의 X축 날짜 동기화
- 이벤트 태그(발산/수렴)를 상단 차트에도 표시 (수직선 또는 마커)

### Stage D: 채팅 UX 개선 (CR.5~CR.6)

**CR.5 스트림 시작 전 대기 UX** `[M]`

Backend:
- `chat_service.py`의 `stream_chat()` 시작 시 즉시 `status` SSE 이벤트 발송
  - 하이브리드 경로: `{"type": "status", "data": {"step": "analyzing", "message": "질문 분석 중..."}}`
  - LLM fallback: `{"type": "status", "data": {"step": "thinking", "message": "AI가 생각하고 있어요..."}}`
  - Tool 호출 직전: 기존 `tool_call` 이벤트가 이미 존재 → 프론트에서 활용
- 하이브리드 `_fetch_hybrid_data()` 진입 시: `{"step": "fetching", "message": "데이터 조회 중..."}`

Frontend:
- `useSSE.ts`: `onStatus` 콜백 추가 (SSE `status` 이벤트 처리)
- `ChatPanel.tsx` / `MessageBubble.tsx`:
  - 스트리밍 시작 전: 타이핑 인디케이터 (점 3개 애니메이션)
  - `status` 이벤트 수신 시: 상태 메시지 표시 ("데이터 조회 중..." 등)
  - `text_delta` 첫 수신 시: 인디케이터 → 실제 텍스트로 전환
- CSS: `@keyframes typing` 애니메이션 (점 3개 순차 깜빡임)

**CR.6 넛지 질문 템플릿 응답** `[M]`

현재: 넛지 질문 칩 클릭 → 일반 채팅과 동일하게 LLM 호출
변경: 넛지 질문 → 하이브리드 분류기 매칭 보장 → 템플릿 응답

Backend:
- `classifier.py`: 넛지 질문 텍스트가 반드시 분류되도록 패턴 보강
  - 현재 넛지 질문: "어떤 자산들이 비슷하게 움직이나요?" → SIMILAR_ASSETS 매칭 확인
  - 매칭 안 되는 넛지 질문이 있으면 패턴 추가
- `templates.py`: 넛지 질문용 응답이 기존 템플릿으로 충분한지 검증
- 대안: `chat_service.py`에서 넛지 질문 여부를 프론트에서 플래그로 전달
  - `SendMessageRequest`에 `is_nudge: bool = False` 필드 추가
  - `is_nudge=True`이면 반드시 하이브리드 경로 + 분류 실패해도 첫 번째 관련 템플릿 사용
  - LLM fallback 방지

Frontend:
- `NudgeQuestions.tsx` → `ChatPanel.tsx`: 넛지 클릭 시 `is_nudge=true` 전달
- `api/chat.ts`: `sendMessageSSE`에 `is_nudge` 파라미터 추가

### Stage E: 통합 검증 (CR.7)

**CR.7 Phase C-rev 통합 검증** `[M]`
- Backend: pytest 전체 통과 + ruff check clean
- Frontend: tsc --noEmit + vite build 성공
- 브라우저 확인:
  - [ ] 종목명 표시 (히트맵, Scatter, Spread, 그룹 카드)
  - [ ] 그래프 설명 텍스트
  - [ ] 상관계수 분포 제거 확인
  - [ ] 히트맵 셀 클릭 → Scatter 강조 + Spread 로드
  - [ ] 3종목 그룹 페어 선택
  - [ ] 정규화 가격 오버레이 차트
  - [ ] Z-score 하단 차트
  - [ ] 채팅 대기 인디케이터 + 상태 메시지
  - [ ] 넛지 질문 → 빠른 템플릿 응답 (LLM 미호출)
  - [ ] LangSmith 트레이스 확인
- 프로덕션 배포 + 브라우저 E2E

## 5. Task Breakdown

| # | Task | Size | 의존성 | Stage |
|---|------|------|--------|-------|
| CR.1 | 종목명 매핑 + 그래프 설명 | M | - | A |
| CR.2 | 상관계수 분포 삭제 | S | - | B |
| CR.3 | 히트맵 셀 클릭 → Scatter+Spread 연동 | L | CR.1 | B |
| CR.4 | 정규화 가격 오버레이 + Z-score 하단 | L | CR.1, CR.3 | C |
| CR.5 | 채팅 대기 UX (타이핑 인디케이터 + 상태) | M | - | D |
| CR.6 | 넛지 질문 템플릿 응답 보장 | M | - | D |
| CR.7 | 통합 검증 | M | CR.1~CR.6 | E |

**Total**: 7 tasks (S:1, M:4, L:2)

## 6. Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| 히트맵 셀 클릭 영역 작음 (7x7) | 셀 사이즈 최소 48px, hover 피드백 |
| 정규화 가격 오버레이에서 스케일 차이 큼 | base=100 정규화로 해결 (이미 계산됨) |
| 넛지 질문 분류기 누락 | is_nudge 플래그로 fallback 방지 |
| 2-패널 차트 모바일 레이아웃 | 세로 스택 (상단 가격, 하단 z-score) |

## 7. Dependencies

**내부**:
- `asset_master` 테이블 (종목명)
- `spread_service.compute_spread()` (정규화 가격 데이터 이미 계산 중)
- `hybrid/classifier.py`, `hybrid/templates.py` (넛지 분류)
- `chartActionStore` (히트맵 → Scatter/Spread 연동)

**외부 (신규 없음)**: 기존 패키지로 충분
