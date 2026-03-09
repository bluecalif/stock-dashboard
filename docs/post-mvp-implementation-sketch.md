# Post-MVP 구현 스케치 (초안 기반 상태 리뷰)

> 기준 문서: `docs/post-mvp-draft.md`  
> 작성일: 2026-03-09

## 1) Objective

- 현재 MVP(데이터 수집/분석/API/대시보드) 위에 `Interactive + 사용자 맞춤형 경험`을 추가한다.
- 핵심 목표는 아래 5가지를 제품 흐름으로 연결하는 것이다.
- Auth
- Chatbot
- Memory (사용자 히스토리)
- 숫자/테이블 데이터 검색(Vector + SQL 하이브리드)
- 그래프 커스터마이징(대화 기반 반영)

## 2) Scope

- 포함
- 사용자 인증/권한 체계
- 대화형 질의 API 및 UI
- 사용자별 메모리 저장/조회
- 분석 데이터 검색 계층(메타데이터 + 임베딩 인덱스)
- 차트 설정 저장/재호출 및 대화 반영

- 제외(이번 스케치 범위 밖)
- 모델 학습 파이프라인 자체 개발
- 멀티테넌트 과금/플랜 시스템
- 실시간 스트리밍(초저지연 웹소켓 틱 데이터)

## 3) Current Status Review (draft 대비)

- 완료된 기반
- 백엔드: FastAPI + Router/Service/Repository + 시계열/백테스트 DB 모델
- 프론트: React 라우팅 + 분석 대시보드 페이지 6종
- 운영: CI/CD, 배포, 스케줄 수집 파이프라인(계획/부분 정리)

- draft 항목 대비 미구현/부분
- Auth: 미구현
- Chatbot: 미구현
- Memory(User RLS): 미구현
- Vector DB/검색 계층: 미구현
- 그래프 Custom 대화 반영: 미구현
- Onboard Agent: 미구현

- 결론
- MVP 데이터/분석 기반은 충분하며, Post-MVP는 “사용자 계층 + 대화 계층 + 개인화 계층” 추가가 핵심이다.

## 4) Assumptions

- DB는 PostgreSQL을 계속 사용한다.
- LLM은 외부 API 연동(Managed)으로 시작하고, 모델 교체 가능하도록 어댑터 패턴을 둔다.
- 임베딩 저장은 PostgreSQL `pgvector` 또는 별도 Vector DB 중 하나를 선택 가능하게 설계한다.
- 보안 기본선: JWT(또는 세션 토큰) + 서버측 권한 검증 + 감사 로그.

## 5) Target Architecture (간단 스케치)

1. `Auth Service`
2. `Conversation Service`
3. `Memory Service`
4. `Context Retrieval Service (SQL + Vector)`
5. `Chart Personalization Service`

요청 흐름:
1. 사용자가 질문/요청 전송
2. Auth 확인 후 사용자 컨텍스트 로드
3. Retrieval이 정형 데이터(SQL) + 유사도 검색(Vector) 결합
4. Chatbot 응답 + UI 액션(JSON patch 형태) 생성
5. 사용자 메모리/대화/차트 설정 저장

## 6) Interfaces (초안 API)

- 인증
- `POST /v1/auth/signup`
- `POST /v1/auth/login`
- `POST /v1/auth/refresh`
- `GET /v1/auth/me`

- 대화
- `POST /v1/chat/sessions`
- `GET /v1/chat/sessions/{session_id}`
- `POST /v1/chat/sessions/{session_id}/messages`

- 메모리
- `GET /v1/memory`
- `POST /v1/memory`
- `DELETE /v1/memory/{memory_id}`

- 차트 커스텀
- `GET /v1/preferences/charts`
- `PUT /v1/preferences/charts/{preset_id}`

- 검색/컨텍스트
- `POST /v1/retrieval/query` (내부용 또는 관리자용)

## 7) Data Model Sketch

- `users` (id, email, password_hash, created_at, status)
- `user_sessions` (session_id, user_id, refresh_token_hash, expires_at)
- `chat_sessions` (id, user_id, title, created_at, updated_at)
- `chat_messages` (id, session_id, role, content, tool_payload, created_at)
- `user_memories` (id, user_id, kind, key, value_json, importance, updated_at)
- `chart_presets` (id, user_id, page, config_json, is_default, updated_at)
- `retrieval_chunks` (id, source_type, source_ref, text, metadata_json, embedding)

권한 원칙:
- 모든 사용자 데이터 테이블은 `user_id` 기준 접근 제어.
- PostgreSQL RLS 적용 시 앱 레벨 필터와 이중 방어.

## 8) Implementation Phases

### Phase A: Auth + 사용자 컨텍스트

- 회원가입/로그인/토큰 갱신
- 백엔드 의존성 주입에 사용자 컨텍스트 추가
- 프론트 라우트 가드 및 로그인 상태 저장

산출물:
- auth router/service/repository
- users/session migration
- 로그인 UI

### Phase B: Chatbot 기본 루프

- 채팅 세션/메시지 저장
- LLM 어댑터 + 프롬프트 템플릿 계층
- 답변과 함께 구조화된 UI 액션 스키마 반환(예: 차트 기간 변경)

산출물:
- chat API + chat DB
- LLM provider adapter
- 채팅 패널 UI

### Phase C: Memory + Retrieval

- 사용자 메모리 CRUD
- 정형 데이터 질의기(SQL) + 임베딩 검색기(Vector) 결합
- 프롬프트에 “최근 대화 + 저장 메모리 + 검색 결과” 주입

산출물:
- memory API
- retrieval service
- 벡터 인덱싱 배치 스크립트

### Phase D: 그래프 커스터마이징 통합

- 차트 preset 저장/복원
- 챗봇 응답의 UI 액션을 프론트 상태로 반영
- “설정 기억하기” 토글 및 사용자 기본값 적용

산출물:
- preferences API
- chart preset UI
- chat-to-chart action reducer

### Phase E: Onboard Agent + 운영 안정화

- 첫 사용자 온보딩 플로우(관심 자산, 전략, 알림 설정)
- 품질 지표(응답시간/정확도/실패율) 모니터링
- 안전장치(프롬프트 인젝션/권한 우회/비용 제한)

## 9) Test Strategy

- 단위 테스트
- auth 토큰/권한 검증
- chat/memory/retrieval 서비스 로직
- chart action schema 검증

- 통합 테스트
- 로그인 → 대화 → 메모리 저장 → 재질의 시 컨텍스트 반영
- 사용자 A/B 데이터 격리 검증(RLS 또는 앱 레벨)

- E2E 테스트
- 대시보드에서 자연어 요청으로 차트 변경
- 세션 재접속 시 설정/메모리 복원

- 운영 테스트
- 부하 테스트(동시 세션)
- 장애 주입(LLM timeout, vector 검색 실패)

## 10) Risks

- LLM 응답 변동성으로 UI 액션이 불안정할 수 있음
- 완화: 엄격한 액션 스키마(JSON schema) + 서버 검증 + fallback

- RLS/권한 누락 시 데이터 노출 위험
- 완화: DB RLS + API 레벨 `user_id` 검증 + 감사 로그

- 검색 품질 미흡 시 답변 신뢰도 저하
- 완화: SQL 우선 + Vector 보조, 출처 표기, 재랭킹 규칙

- 비용 증가(토큰/임베딩/저장소)
- 완화: 캐싱, 요약 저장, 배치 임베딩, 쿼터 제한

## 11) 실행 우선순위 (제안)

1. Phase A(Auth) + 최소 채팅 저장
2. Phase B(Chatbot 기본 루프)
3. Phase D(차트 커스텀 연동) 일부를 먼저 적용해 사용자 체감 확보
4. Phase C(Memory + Retrieval)로 정확도/개인화 강화
5. Phase E(Onboarding/운영 고도화)

