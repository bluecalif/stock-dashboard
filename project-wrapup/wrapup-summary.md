# Project Wrapup — Stock Dashboard

> Generated: 2026-04-10
> 역할: **프로젝트 성과 문서가 아니라, 문서 패키지 전체의 입구**

## 이 패키지로 무엇을 얻을 수 있는가

**데이터 수집 → 분석 → 시각화 → AI 채팅** 파이프라인을 갖춘 풀스택 대시보드를 만들 때, 42일간 198커밋·874테스트를 통해 검증된 개발 순서, 실수 방지 규칙, 재사용 가능한 코드 패턴을 제공한다.

## 읽는 순서

1. **이 문서** — 전체 파악, Top 5 실수/패턴, 1페이지 개발 순서
2. **[project-blueprint.md](project-blueprint.md)** — 개발 순서 결정 (Core Path 7단계 + Expansion Path 6단계)
3. **[lessons-learned.md](lessons-learned.md)** — 실수 방지 플레이북 (high-impact 7건 상세 + 일반 38건)
4. **[reusable-patterns/](reusable-patterns/)** — 코드 재사용 (9개 검증된 스니펫)
5. **[lessons-learned.json](lessons-learned.json)** — 크로스 프로젝트 교훈 DB

## 프로젝트 개요

| 항목 | 값 |
|------|-----|
| Phase | 13/13 완료 (Core 7 + Expansion 6) |
| 테스트 | 874개 |
| 커밋 | 198개 |
| 기간 | 2026-02-10 ~ 2026-03-22 (42일) |
| 태스크 | MVP 83 + Post-MVP 112 = 195개 |

## 가장 중요한 실수 Top 5

| 순위 | 교훈 ID | 한 줄 요약 | 예방 규칙 |
|------|---------|-----------|----------|
| 1 | T-003 | 요청 스코프 DB 세션을 백그라운드 태스크에 전달 | **자체 `SessionLocal()` 생성 필수.** 요청 스코프 세션 절대 전달 금지 |
| 2 | T-005 | `order_by(asc) + limit=N` 함정 | **"limit이 어느 쪽 끝에서 자르는가" 확인.** desc 전용 함수 분리 |
| 3 | T-010 | LangChain `with_structured_output` 프로덕션 실패 | **JSON Mode + 수동 파싱 사용.** 고수준 추상화보다 저수준 직접 제어 |
| 4 | T-023 | reasoning 모델 호환성 (느려짐으로 발현) | **새 모델 도입 시 reasoning 여부 확인.** non-reasoning이 4-7배 빠른 작업 존재 |
| 5 | A-004 | 대시보드 ↔ Agentic 데이터 소스 불일치 | **동일 서비스 레이어 공유.** 새 API 추가 시 LLM 툴도 동시 업데이트 |

→ 상세: [lessons-learned.md](lessons-learned.md) | DB: [lessons-learned.json](lessons-learned.json)

## 바로 재사용할 수 있는 패턴 Top 5

| 순위 | 패턴 | 해결 문제 | 복붙 가능? |
|------|------|----------|-----------|
| 1 | [`router-service-repo.py`](reusable-patterns/router-service-repo.py) | 3계층 분리로 테스트 용이성 확보 | 수정 필요 (모델/스키마 교체) |
| 2 | [`langraph-classifier.py`](reusable-patterns/langraph-classifier.py) | JSON Mode + fallback 기반 LLM 분류 | 수정 필요 (프롬프트/카테고리 교체) |
| 3 | [`idempotent-upsert.py`](reusable-patterns/idempotent-upsert.py) | PostgreSQL ON CONFLICT 기반 멱등 적재 | 수정 필요 (테이블/컬럼 교체) |
| 4 | [`jwt-auth-flow.py`](reusable-patterns/jwt-auth-flow.py) | JWT + Refresh Token Rotation 인증 | 수정 필요 (시크릿/TTL 교체) |
| 5 | [`axios-interceptor-refresh.ts`](reusable-patterns/axios-interceptor-refresh.ts) | Bearer 주입 + 401 동시 요청 큐 | 거의 복붙 가능 |

→ 전체 목록: [reusable-patterns/](reusable-patterns/) (9개 패턴)

## 권장 개발 순서 1페이지 요약

```
Core Path (반드시 먼저)
  Phase 1: Skeleton + DB        ──→ 스키마 확정, CASCADE FK
  Phase 2: Data Collector       ──→ 외부 소스 연동, UPSERT
  Phase 3: Analysis Engine      ──→ 팩터, 전략, 백테스트
  Phase 4: REST API             ──→ 3계층 분리, Pydantic
  Phase 5: Frontend Dashboard   ──→ Canonical Form, 시각화
  Phase 6: Deploy & Ops         ──→ Dockerfile, 환경변수 체크리스트
  Phase 7: Scheduled Collection ──→ Cron, UTC

Expansion Path (Core 완료 후)
  Phase A: Authentication       ──→ JWT Refresh Rotation
  Phase B: AI Chatbot           ──→ SSE 스트리밍, LLM 기본 설정
  Phase C~D: 분석 고도화         ──→ 상관, 지표, Canonical Form 검증
  Phase E: Strategy Viz         ──→ 에쿼티 커브, tsc -b 확인
  Phase F: Agentic AI           ──→ 2-Step LLM, Cache Warmup, JSON Mode
  Phase G: Context & Memory     ──→ 세션 분리, 히스토리 요약
```

→ 상세 (gate 조건, 선행/완료/금지): [project-blueprint.md](project-blueprint.md)

## 후속 과제

- [x] ~~Reporter LLM 34.8s → 5.8s~~ — gpt-4.1-mini 분리 완료
- [x] ~~Cold Start 12s → ~1.3s~~ — Cache Warmup 완료
- [ ] 프로덕션 배포 테스트 (최종 확인)
- [ ] 실시간 데이터 (WebSocket 스트리밍)
- [ ] 자산 확장 (ETF, 추가 암호화폐)
- [ ] 전략 확장 (포트폴리오 최적화, 리스크 패리티)
- [ ] Hantoo REST API fallback (v0.9+)
