# Project Wrapup — Stock Dashboard

> Generated: 2026-03-22

## 프로젝트 개요

7개 자산(KOSPI200, 삼성전자, SK하이닉스, SOXL, BTC, Gold, Silver)의 일봉 데이터를 수집·분석·시각화하는 풀스택 대시보드. 15개 팩터, 3개 전략 백테스트, LangGraph 기반 AI 채팅 상담을 제공.

## 최종 상태

- **Phase**: 12/12 Phase 완료 (MVP 0~7 + Post-MVP A~G)
- **테스트**: 874개
- **커밋**: 194개
- **기간**: 2026-02-10 ~ 2026-03-22
- **태스크**: MVP 83 + Post-MVP 112 = 195 tasks 완료

## 핵심 성과

1. **풀스택 파이프라인**: 수집 → DB → 분석 → API → 대시보드 → AI 채팅 전 구간 구현
2. **Agentic AI 채팅**: 2-Step LLM (Classifier 8초 + Reporter 5.8초) + 사용자 맥락 인식 + 모델 분리 최적화
3. **869개 테스트**: Router-Service-Repository 3계층 분리로 높은 테스트 커버리지
4. **프로덕션 배포**: Railway(Backend) + Vercel(Frontend) + GitHub Actions(CI/CD + Daily Cron)
5. **사용자 경험**: Ice-breaking 온보딩, 대화 메모리, 프로필 기반 응답 톤 조절

## 교훈 요약

| # | 교훈 | Impact |
|---|------|--------|
| T-03 | 백그라운드 태스크에 요청 스코프 DB 세션 전달 금지 | High |
| T-05 | `order_by(asc) + limit=N` 함정 — 전수조사 필수 | High |
| T-09 | OpenAI 529 에러 → 서버 문제로 단정 금지, 클라이언트 측 먼저 확인 | High |
| T-10 | LangChain `with_structured_output` 대신 JSON Mode 사용 | High |
| T-23 | reasoning 모델(gpt-5-mini/nano) 호환성 — temperature 미지원, 느려짐으로 발현 | High |
| A-01 | UX와 데이터 Flow 정합성 — Canonical Form으로 중앙 관리 | High |

→ 상세: [lessons-learned.md](lessons-learned.md)
→ DB: [lessons-learned.json](lessons-learned.json)

## 재사용 패턴

| 패턴 | 파일 | 설명 |
|------|------|------|
| JWT Auth Flow | `jwt-auth-flow.py` | 비밀번호 해싱, 토큰 생성/검증, Refresh Rotation |
| FastAPI DI | `fastapi-dependency-injection.py` | DB 세션 관리, 인증 필수/선택 |
| Router-Service-Repo | `router-service-repo.py` | 3계층 분리 패턴 |
| Zustand Auth Store | `zustand-auth-store.ts` | 토큰 영속성 + 자동 갱신 |
| Axios Interceptor | `axios-interceptor-refresh.ts` | Bearer 주입 + 401 동시 요청 큐 |
| LangGraph Classifier | `langraph-classifier.py` | JSON Mode + fallback + 컨텍스트 빌드 |
| Strategy ABC | `strategy-abc.py` | 전략 추상 클래스 + action labeling |
| CASCADE FK Models | `cascade-fk-models.py` | SQLAlchemy 2.0 UUID PK + CASCADE |
| Idempotent UPSERT | `idempotent-upsert.py` | ON CONFLICT DO UPDATE + chunk + job 추적 |

→ 상세: [reusable-patterns/](reusable-patterns/)

## 설계 순서도 요약

1. Skeleton + DB
2. Data Collector
3. Analysis Engine
4. REST API
5. Frontend Dashboard
6. Deploy & Ops
7. Scheduled Collection
8. Authentication
9. AI Chatbot
10. 분석 페이지 고도화 (상관, 지표, 피드백)
11. Strategy Visualization
12. Agentic AI (2-Step LLM)
13. Context & Memory

→ 상세: [project-blueprint.md](project-blueprint.md)

## 후속 과제

- [x] ~~Reporter LLM 응답 시간 ~22초 → 성능 최적화~~ — **완료** (gpt-4.1-mini 분리, 34.8s→5.8s, `ec2995b`)
- [ ] 프로덕션 배포 테스트 (최종 확인)
- [ ] 실시간 데이터 (WebSocket 스트리밍)
- [ ] 자산 확장 (ETF, 추가 암호화폐)
- [ ] 전략 확장 (포트폴리오 최적화, 리스크 패리티)
- [ ] Hantoo REST API fallback (v0.9+)
