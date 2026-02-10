---
description: 개발 태스크에 대한 종합 계획 및 추적 문서 생성
argument-hint: 계획할 내용 (예: "FDR collector pipeline", "backtest engine")
---

# 개발 문서 생성 (Dev Docs Generator)

**Task:** $ARGUMENTS

## Instructions

### 1. 요청 분석 (Analyze Request)

- 범위(scope)와 영향도(impact) 파악
- 관련 컴포넌트 식별 (collector, research_engine, api, dashboard)
- 기존 설계 문서와의 연관성 확인

### 2. 관련 문서 검토 (Review Existing Docs)

프로젝트 문서 확인:
- `docs/masterplan-v0.md` - 마스터플랜 (아키텍처, 스키마, 마일스톤)
- `docs/session-compact.md` - 현재 진행 상태
- `docs/data-accessibility-plan.md` - 데이터 접근성 검증 계획
- `docs/data-accessibility-report.md` - 데이터 접근성 검증 결과

### 3. 계획 구조 (Plan Structure)

다음 섹션을 포함한 계획 작성:

```
1. Summary (개요)
   - 목적, 범위, 예상 결과물

2. Current State (현재 상태)
   - 기존 구현/설계 상태
   - 관련 파일 목록

3. Target State (목표 상태)
   - 완료 후 기대 상태
   - 주요 변경 사항

4. Implementation Phases (구현 단계)
   - Phase 1, 2, 3... 순차적 단계
   - 각 단계별 목표와 산출물

5. Task Breakdown (태스크 목록)
   - 구체적 액션 아이템
   - 노력도: S/M/L/XL
   - 의존성 명시

6. Risks & Mitigation (리스크 및 완화)

7. Dependencies (의존성)
```

### 4. 파일 생성 (Generate Files)

**위치:** `dev/active/[task-name]/`

| 파일 | 용도 |
|------|------|
| `[task-name]-plan.md` | 종합 계획 문서 |
| `[task-name]-context.md` | 핵심 파일, 결정사항, 참조 |
| `[task-name]-tasks.md` | 체크리스트 형식 진행 추적 |

**파일 헤더:**
```markdown
# [Task Name]
> Last Updated: YYYY-MM-DD
> Status: Planning | In Progress | Review | Done
```

### 5. 프로젝트 컨벤션 체크 (Convention Checklist)

**데이터 관련:**
- [ ] OHLCV 표준 스키마 준수 (asset_id, date, open, high, low, close, volume, source, ingested_at)
- [ ] FDR primary source 사용 (모든 자산)
- [ ] price_daily PK: (asset_id, date, source)

**API 관련:**
- [ ] Router → Service → Repository 레이어 분리
- [ ] Pydantic 스키마 정의
- [ ] 의존성 주입 패턴

**수집 관련:**
- [ ] idempotent UPSERT
- [ ] 지수 백오프 재시도
- [ ] 정합성 검증 (고가/저가 역전, 음수 가격, 중복)

### 6. 관련 스킬 참조

| Skill | 용도 |
|-------|------|
| `backend-dev` | FastAPI, SQLAlchemy, collector, research_engine 패턴 |

---

## Output Format

```
생성 완료

dev/active/[task-name]/
├── [task-name]-plan.md      (종합 계획)
├── [task-name]-context.md   (컨텍스트)
└── [task-name]-tasks.md     (태스크 추적)

요약:
- Phases: N개
- Tasks: N개 (S: n, M: n, L: n, XL: n)
- Dependencies: [목록]
```
