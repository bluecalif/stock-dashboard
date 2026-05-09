# Phase C-rev2: 상관도 페이지 2차 피드백 반영
> Last Updated: 2026-03-14
> Status: Complete
> Source: `docs/post-mvp-feedback.md` + `docs/session-compact.md` (프로덕션 2차 리뷰)

## 1. Summary (개요)

**목적**: Phase C-rev 완료 후 프로덕션 2차 브라우저 리뷰에서 수집된 피드백 3건 구현
**범위**: 수익률 산점도 추가 + 넛지 칩 상시 표시 + 질문 분류 전략 개선
**원칙**: Phase D 진입 전 완료 — 기존 Phase C-rev 코드 위에 수정/확장

## 2. Current State (현재 상태)

- Phase C-rev 7/7 Tasks 완료, 프로덕션 배포 완료 (`d7f7a8c`)
- 테스트: 561 passed, 7 skipped, ruff/tsc/vite clean
- 히트맵 셀 클릭 → SpreadChart **3-패널** (수익률 산점도 + 정규화 가격 + Z-score)
- 넛지 칩: 채팅 상단에 **항상** 표시, 스트리밍 중 비활성화
- 질문 분류: `is_nudge=True` → regex 분류, `is_nudge=False` → LLM fallback

## 3. Target State (목표 상태)

- 히트맵 셀 클릭 → **3-패널** (수익률 산점도 + 정규화 가격 + Z-score)
- 넛지 칩: 답변 후에도 채팅 상단에 **항상** 표시 (스트리밍 중 비활성화)
- 질문 분류: `is_nudge=True` → 템플릿, `is_nudge=False` → LLM fallback (regex 스킵)

## 4. Implementation Stages

### Stage A: 질문 분류 전략 개선 (CR2.1)

**CR2.1 is_nudge 기반 분류 분기** `[S]`

Backend — `chat_service.py` 한 곳 수정:
- `stream_chat()`에서 `classify_question()` 호출을 `is_nudge=True`일 때만 실행
- `is_nudge=False` → `category = None` → 바로 LangGraph LLM fallback
- 나머지 로직(is_nudge 기본 카테고리 폴백, 템플릿 응답) 그대로 유지

```python
# 변경 전 (172행 근처)
category = classify_question(content, ctx)

# 변경 후
if is_nudge:
    category = classify_question(content, ctx)
else:
    category = None
```

**장기 비전 참고** (Phase D/E에서 구현):
- LLM 또는 벡터 기반 질문 Classification 도입
- 페이지 해당 여부 판단 + 비해당 시 페이지 이동 제안
- Structured Output 형식 LLM 응답
- 상세: `docs/post-mvp-feedback.md` 채팅 추가 개선 섹션

### Stage B: 넛지 칩 상시 표시 (CR2.2)

**CR2.2 넛지 칩 항상 표시 + 스트리밍 중 비활성화** `[S]`

Frontend — `ChatPanel.tsx`:
- `messages.length === 0` 조건 밖으로 `NudgeQuestions` 이동
- 메시지 영역 상단에 항상 렌더링
- `disabled={isStreaming}` prop 전달

```
변경 전:
{messages.length === 0 && (
  <div>
    <p>안내 텍스트</p>
    <NudgeQuestions ... />
  </div>
)}

변경 후:
<NudgeQuestions pageId={...} onSelect={...} disabled={isStreaming} />
{messages.length === 0 && (<안내 텍스트/>)}
{messages.map(...)}
```

Frontend — `NudgeQuestions.tsx`:
- Props에 `disabled?: boolean` 추가
- `disabled`일 때 `opacity-50 pointer-events-none` 적용

### Stage C: 수익률 산점도 추가 (CR2.3)

**CR2.3 ReturnScatterChart + 3-패널 구조** `[M]`

설계 결정: **수익률은 프론트엔드에서 계산** (API 변경 불필요)
- `SpreadResponse.normalized_prices` (base=100) 데이터가 이미 존재
- `returns[i] = (price[i] - price[i-1]) / price[i-1]` 단순 산술

Frontend — `ReturnScatterChart.tsx` (신규):
- Props: `normedA: number[], normedB: number[], dates: string[], nameA: string, nameB: string`
- 정규화 가격으로부터 일별 수익률(%) 계산
- Recharts `ScatterChart` 사용 (기존 `ScatterPlotChart.tsx` 패턴 참고)
- X축=종목A 수익률(%), Y축=종목B 수익률(%)
- Tooltip: 날짜, 양 종목 수익률(%) 표시
- 높이: 기존 패널과 일관 (200px 내외)

Frontend — `SpreadChart.tsx` 수정:
- `ReturnScatterChart` import
- 3-패널 구조:
  1. **수익률 산점도** (신규) — `normalized_prices` 존재 시만
  2. 정규화 가격 오버레이 (기존)
  3. Z-Score 추이 (기존)

### Stage D: 통합 검증 (CR2.4)

**CR2.4 Phase C-rev2 통합 검증** `[S]`
- Backend: pytest 전체 통과 + ruff check clean
- Frontend: tsc --noEmit + vite build 성공
- 브라우저 확인:
  - [ ] 히트맵 셀 클릭 → 3-패널 (산점도 + 정규화 + Z-score)
  - [ ] 양의 상관 높은 페어 → 산점도 점 우상향 분포
  - [ ] 넛지 칩 상시 표시 (메시지 있어도 유지)
  - [ ] 스트리밍 중 칩 비활성화 → 완료 후 재활성화
  - [ ] 사용자 직접 질문 → LLM 자유 응답 (템플릿 아님)
  - [ ] 넛지 칩 클릭 → 기존 템플릿 응답 유지

## 5. Task Breakdown

| # | Task | Size | 의존성 | Stage |
|---|------|------|--------|-------|
| CR2.1 | is_nudge 기반 분류 분기 | S | - | A |
| CR2.2 | 넛지 칩 상시 표시 | S | - | B |
| CR2.3 | 수익률 산점도 + 3-패널 | M | - | C |
| CR2.4 | 통합 검증 | S | CR2.1~CR2.3 | D |

**Total**: 4 tasks (S:3, M:1)

## 6. Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| 수익률 계산 정밀도 (프론트엔드 JS) | 정규화 가격이 이미 float64, 충분한 정밀도 |
| 3-패널 높이 과다 (모바일) | 각 패널 높이 축소 + 세로 스크롤 허용 |
| 넛지 칩 상시 표시로 화면 공간 부족 | 칩 영역 compact (py-2, text-xs, 가로 스크롤) |

## 7. Dependencies

**내부**:
- `SpreadResponse.normalized_prices` (Phase C-rev에서 추가됨)
- `chat_service.py` — `is_nudge` 플래그 (Phase C-rev에서 추가됨)
- `NudgeQuestions.tsx`, `ChatPanel.tsx` (Phase C에서 생성됨)
- `ScatterPlotChart.tsx` — Recharts ScatterChart 패턴 참고

**외부 (신규 없음)**: 기존 패키지(Recharts)로 충분
