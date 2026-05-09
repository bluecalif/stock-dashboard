# Post-MVP 구현 스케치

> 기준 문서: `docs/post-mvp-draft.md`
> 업데이트: 2026-03-10

## 1) Objective

- 현재 MVP를 `조회형 대시보드`에서 `대화형 분석 워크스페이스`로 확장한다.
- 사용자가 자연어로 질문하면, 시스템은 아래를 하나의 흐름으로 처리해야 한다.
- 분석 맥락 설명
- 차트/그래프 커스터마이징 반영
- 지표 시그널 해석
- 전략 성과 비교
- 사용자별 메모리 축적

핵심 제품 정의:
- 단순 시각화가 아니라 `사용자와 interactive`한 분석 경험 제공
- 숫자/테이블 중심 데이터를 초심자도 이해 가능한 설명으로 구조화
- 차트, 지표, 전략, 추천 흐름을 하나의 대화 루프에 통합

## 2) Scope

포함:
- Auth 및 사용자 컨텍스트
- Chatbot 기반 질의/응답
- 사용자 메모리 저장 및 재호출
- 정형 데이터(SQL) + 임베딩(Vector) 혼합 검색
- 그래프 커스터마이징과 대화 응답 연동
- 상관/지표 시그널/전략 페이지 재편
- 온보딩 에이전트 초안

제외:
- 자체 파운데이션 모델 학습
- 실시간 초단위 체결 스트리밍 최적화
- 과금/플랜/조직 단위 멀티테넌시

## 3) Product Direction From Draft

`post-mvp-draft` 기준으로 제품은 아래 4개 축을 함께 해결해야 한다.

### A. Interactive Layer

- Chatbot이 단순 Q&A가 아니라 그래프 변경 요청까지 처리
- 대화 내용이 실시간으로 그래프 설정에 반영
- 후속 질문에서도 직전 맥락과 사용자 선호를 유지

### B. Information Structuring Layer

- 숫자/테이블 데이터에 대해 설명 가능한 컨텍스트 제공
- 자산 관계, 지표 의미, 전략 결과를 텍스트와 차트로 함께 제시
- Vector DB는 자유 질의 보조용이고, 핵심 수치 계산은 SQL/백엔드 분석 로직이 우선

### C. Personalization Layer

- 로그인 사용자 기준 대화 이력 저장
- 사용자별 메모리 및 차트 프리셋 유지
- 온보딩 단계에서 관심 자산/전략/알림 선호를 수집

### D. UX Simplification Layer

- 전체 페이지 설명을 쉬운 용어로 보강
- 가격 차이 때문에 비교가 어려운 경우 정규화 표시를 선택 가능하게 제공
- 분석 용어는 가능한 한 초심자 기준으로 재표현

## 4) Functional Requirements

### 4-1. 공통 기능

- 인증된 사용자는 자신의 대화, 메모리, 차트 설정만 조회 가능해야 한다.
- 챗봇 응답은 텍스트와 함께 구조화된 UI 액션을 반환해야 한다.
- 모든 분석 응답은 가능한 경우 근거 데이터와 계산 기준을 함께 표시해야 한다.
- 전문 용어만 나열하지 말고, 쉬운 표현을 함께 제공해야 한다.

### 4-2. 페이지 구조 재편

- 페이지는 `홈 / 가격 / 상관 / 지표 시그널 / 전략` 구조로 정리한다.
- 기존 팩터와 시그널 페이지는 `지표 시그널`로 통합한다.
- 전략 페이지는 지표 시그널에 기반한 성과를 보여주어야 한다.

### 4-3. 그래프별 시나리오

#### 상관 페이지

- 관계도가 높은 자산을 그룹으로 묶어 보여준다.
- 특정 자산과 상관도가 높은 자산에 대한 설명을 제공한다.
- 과거 수익률 흐름을 바탕으로 유사 움직임 자산을 추천한다.
- 자산 간 교차점 클릭 시 scatter plot을 보여준다.
- 챗봇 요청으로 scatter plot이나 비교 자산을 즉시 변경할 수 있어야 한다.

#### 지표 시그널 페이지

- RSI, MACD, Bollinger Band, ATR를 우선 지원한다.
- 각 지표는 단순 수치가 아니라 어떤 상황을 의미하는지 설명해야 한다.
- MACD: 모멘텀 관점 설명
- RSI(14) + Bollinger: 되돌림 관점 설명
- Bollinger + ATR: 변동성/위험 회피 관점 설명
- 요청 시 가격과 지표를 오버레이해 보여준다.
- 가격 차이가 커 비교가 어려우면 정규화 보기 옵션을 제공한다.
- 핵심 지표들에 대해 시그널 상태를 명확히 표시한다.
- 챗봇 요청으로 지표 표시/숨김, 기간, 오버레이를 변경할 수 있어야 한다.

#### 전략 페이지

- 모멘텀 vs 되돌림(Contrarian) vs 위험회피 전략을 비교한다.
- 최근 6개월, 1년, 2년 기준으로 성과를 비교한다.
- 종목 간 또는 전략 간 성과 비교를 지원한다.
- 성과 표현은 `누적 수익 흐름`과 `마지막 평가금액` 중심으로 보여준다.
- `전략 적합도`, `전략 매치도`, `성공 확률` 같은 추상 점수는 사용하지 않는다.
- 비교 결과는 초심자도 읽기 쉬운 schematic 또는 카드형 UI로 제공 가능해야 한다.

## 5) Assumptions

- 기존 백엔드/DB 구조는 유지하고, Postgres를 주 저장소로 사용한다.
- LLM은 외부 API를 사용하되 공급자 교체가 가능한 어댑터 패턴으로 분리한다.
- 수치 계산과 지표 산출은 애플리케이션 서비스 계층에서 결정적으로 수행한다.
- Vector 검색은 설명/연관 문맥 보조용이며, 원천 데이터 계산 결과를 대체하지 않는다.
- 사용자 데이터 보호를 위해 앱 레벨 권한 검증과 DB 레벨 격리를 함께 적용한다.

## 6) Vector Storage Decision Note

### `pgvector`를 쓰는 경우

- 장점
- 기존 Postgres 안에서 함께 관리할 수 있어 운영이 단순하다.
- 인증/백업/마이그레이션/권한 체계를 한 저장소에 모을 수 있다.
- 초기 데이터 규모가 크지 않을 때 구현 속도가 빠르다.

- 단점
- 대규모 벡터 검색 성능이나 고급 인덱스 옵션은 전용 엔진보다 제한적일 수 있다.
- 분석용 SQL 부하와 벡터 검색 부하가 같은 DB에 모인다.

### 별도 벡터 엔진을 쓰는 경우

- 장점
- 벡터 검색 성능과 확장성이 일반적으로 더 좋다.
- 하이브리드 검색, 필터링, ANN 튜닝 등 검색 기능이 더 풍부한 경우가 많다.
- 메인 Postgres 부하를 분리할 수 있다.

- 단점
- 운영 대상이 하나 더 늘어난다.
- 동기화 파이프라인과 장애 처리 지점이 추가된다.
- 권한/백업/모니터링을 별도로 설계해야 한다.

### 현재 문서 기준 추천

- Post-MVP 초기 단계에서는 `pgvector` 시작이 더 실용적이다.
- 이유는 현재 요구가 `정형 데이터 계산 우선 + 벡터는 보조 검색` 구조이기 때문이다.
- 검색량이 커지거나 검색 품질 튜닝 요구가 강해지면 별도 엔진 분리를 검토한다.

## 7) Target Architecture

### 서비스 구성

1. `Auth Service`
2. `Conversation Service`
3. `Memory Service`
4. `Retrieval Service`
5. `Indicator/Strategy Analysis Service`
6. `Chart Personalization Service`
7. `Onboarding Service`

### 요청 흐름

1. 사용자가 질문 또는 그래프 변경 요청 전송
2. 인증 및 사용자 컨텍스트 확인
3. 요청을 `정보 질의`, `그래프 액션`, `전략 비교`, `설명 요청`으로 분류
4. 정형 데이터 조회와 필요 시 Vector 검색 결합
5. 분석 서비스가 지표/전략 결과 산출
6. 챗봇이 설명 텍스트 + UI 액션 + 근거 메타데이터 생성
7. 대화 이력, 메모리, 사용자 설정 저장

## 8) API / Interface Sketch

### 인증

- `POST /v1/auth/signup`
- `POST /v1/auth/login`
- `POST /v1/auth/refresh`
- `GET /v1/auth/me`

### 대화

- `POST /v1/chat/sessions`
- `GET /v1/chat/sessions/{session_id}`
- `POST /v1/chat/sessions/{session_id}/messages`

요청/응답 원칙:
- 메시지 입력은 자연어 + 현재 화면 컨텍스트를 함께 전달
- 응답은 `answer`, `citations`, `ui_actions`, `memory_updates`를 포함

### 메모리

- `GET /v1/memory`
- `POST /v1/memory`
- `DELETE /v1/memory/{memory_id}`

### 차트/설정

- `GET /v1/preferences/charts`
- `PUT /v1/preferences/charts/{preset_id}`
- `POST /v1/chart-actions/preview`

### 분석/검색

- `POST /v1/retrieval/query`
- `POST /v1/analysis/indicators`
- `POST /v1/analysis/strategies/compare`
- `POST /v1/analysis/correlation/explain`

### 온보딩

- `POST /v1/onboarding/start`
- `POST /v1/onboarding/answers`
- `GET /v1/onboarding/profile`

## 9) Data Model Sketch

- `users` `(id, email, password_hash, created_at, status)`
- `user_sessions` `(id, user_id, refresh_token_hash, expires_at)`
- `chat_sessions` `(id, user_id, title, created_at, updated_at)`
- `chat_messages` `(id, session_id, role, content, tool_payload, created_at)`
- `user_memories` `(id, user_id, kind, key, value_json, importance, updated_at)`
- `chart_presets` `(id, user_id, page, config_json, is_default, updated_at)`
- `onboarding_profiles` `(id, user_id, favorite_assets_json, strategy_prefs_json, alert_prefs_json, updated_at)`
- `retrieval_chunks` `(id, source_type, source_ref, text, metadata_json, embedding)`
- `analysis_snapshots` `(id, analysis_type, asset_scope, params_json, result_json, created_at)`

권한 원칙:
- 사용자 소유 데이터는 모두 `user_id` 기준으로 제어
- RLS 적용 시에도 API 레벨 사용자 검증 유지
- 공용 분석 스냅샷과 사용자 메모리는 저장소를 논리적으로 구분

## 10) Implementation Phases

### Phase A. Auth + 사용자 컨텍스트

- 회원가입/로그인/토큰 갱신 구현
- 프론트 라우트 가드 및 세션 복원
- 백엔드 요청 컨텍스트에 사용자 식별 주입

산출물:
- auth router/service/repository
- users/session migration
- 로그인 UI

### Phase B. Chatbot 기본 루프

- 채팅 세션/메시지 저장
- LLM 어댑터 및 프롬프트 템플릿 계층
- 텍스트 응답 + UI 액션 스키마 반환

산출물:
- chat API
- chat DB schema
- 채팅 패널 UI

### Phase C. 분석 시나리오 API

- 상관도 설명 API
- 지표 계산/해석 API
- 전략 비교 API
- 차트 오버레이/정규화 요청 처리

산출물:
- indicator/strategy/correlation service
- 분석 응답 스키마
- 차트 액션 매핑 규칙

### Phase D. Memory + Retrieval

- 사용자 메모리 CRUD
- 최근 대화 + 저장 메모리 + 관련 분석 문맥 결합
- SQL 우선, Vector 보조 검색 계층 도입

산출물:
- memory API
- retrieval service
- 임베딩 인덱싱 작업

### Phase E. 그래프 커스터마이징 통합

- 차트 preset 저장/복원
- 챗봇의 UI 액션을 프론트 상태 변경으로 연결
- 상관/scatter/지표 오버레이/전략 비교 요청을 실제 차트 반영

산출물:
- preferences API
- chart preset UI
- chat-to-chart reducer

### Phase F. Onboarding + 운영 안정화

- 관심 자산/전략/알림 선호 수집
- 사용자 첫 진입 가이드 구성
- 프롬프트 인젝션, 권한 우회, 비용 한도 방어

산출물:
- onboarding API/UI
- 품질 모니터링 대시보드
- 운영 정책 문서

## 11) Test Strategy

단위 테스트:
- auth 토큰/권한 검증
- 지표 계산 정확성
- 전략 비교 결과 스키마 검증
- chat action schema 검증

통합 테스트:
- 로그인 후 대화 저장/복원
- 사용자별 메모리 격리
- 상관도/지표/전략 API와 챗봇 응답 연결
- chart action 적용 후 프론트 상태 반영

E2E 테스트:
- 자연어로 "RSI 겹쳐 보여줘" 요청 후 차트 오버레이 반영
- "상관 높은 종목 보여줘" 요청 후 그룹/설명/scatter plot 진입
- 전략 페이지에서 기간(6M, 1Y, 2Y) 변경 후 누적 수익 흐름과 마지막 평가금액 반영
- 세션 재접속 후 사용자 설정과 메모리 복원

운영 검증:
- LLM timeout 및 retrieval 실패 fallback
- 분석 API 응답시간 측정
- 사용자 데이터 교차 노출 방지 검증

## 12) Risks

- LLM이 잘못된 UI 액션을 생성할 수 있음
- 완화: 제한된 액션 타입, JSON schema 검증, 서버측 allowlist

- Vector 검색이 수치 근거보다 앞서면 설명 품질이 흔들릴 수 있음
- 완화: 계산 결과를 우선 사용하고, Vector는 보조 근거로만 사용

- 전략 비교가 기간 선택에 과도하게 민감할 수 있음
- 완화: 6개월/1년/2년 비교를 기본 제공하고 계산 기준을 명시

- 사용자 메모리와 공용 분석 컨텍스트가 섞이면 개인화 품질이 저하될 수 있음
- 완화: memory/retrieval source를 명시적으로 분리하고 응답 메타데이터에 출처 포함

## 13) Execution Priority

1. Phase A로 사용자 계층 확보
2. Phase B로 대화 루프 구축
3. Phase C로 draft의 핵심 기능인 상관도/지표/전략 해석 지원
4. Phase E로 대화 결과를 실제 차트 변경까지 연결
5. Phase D로 메모리와 검색 품질 강화
6. Phase F로 온보딩 및 운영 안정화 확장

## 14) Open Decisions

- Vector 저장소는 초기에는 `pgvector`로 시작하고, 분리 필요 시 별도 엔진으로 확장
- scatter plot/overlay/schematic 비교 UI를 기존 프론트 컴포넌트에 확장할지 신규 컴포넌트로 분리할지
- 온보딩 에이전트를 규칙 기반으로 시작할지 LLM 기반으로 시작할지
