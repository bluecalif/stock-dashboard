# Phase C-rev2: 상관도 페이지 2차 피드백 반영 — Context
> Last Updated: 2026-03-14
> Status: Complete

## 1. 핵심 파일

### Backend — 수정 대상
| 파일 | 수정 내용 |
|------|----------|
| `backend/api/services/chat/chat_service.py` | `classify_question()` 호출을 `is_nudge=True`일 때만 실행 |

### Frontend — 수정 대상
| 파일 | 수정 내용 |
|------|----------|
| `frontend/src/components/chat/ChatPanel.tsx` | NudgeQuestions 상시 표시 + disabled prop |
| `frontend/src/components/chat/NudgeQuestions.tsx` | `disabled?: boolean` prop 추가 |
| `frontend/src/components/charts/SpreadChart.tsx` | ReturnScatterChart 통합, 3-패널 구조 |

### Frontend — 신규 파일
| 파일 | 용도 |
|------|------|
| `frontend/src/components/charts/ReturnScatterChart.tsx` | 수익률 X-Y 산점도 컴포넌트 |

### 참고 파일 (읽기만)
| 파일 | 용도 |
|------|------|
| `frontend/src/components/charts/ScatterPlotChart.tsx` | Recharts ScatterChart 사용 패턴 참고 |
| `frontend/src/pages/CorrelationPage.tsx` | 히트맵 → SpreadChart 연동 흐름 |
| `frontend/src/types/api.ts` | SpreadResponse 타입 정의 |
| `frontend/src/store/chatStore.ts` | isStreaming 상태 |
| `backend/api/services/llm/hybrid/classifier.py` | classify_question() 현재 로직 |

## 2. 데이터 인터페이스

### 수익률 산점도 데이터 (프론트엔드 계산)
- 입력: `SpreadResponse.normalized_prices.asset_a/b: number[]` (base=100)
- 계산: `returns[i] = (price[i] - price[i-1]) / price[i-1] * 100` (%)
- 출력: `ScatterChart` 데이터 `{x: returnA, y: returnB, date: string}[]`

### 질문 분류 분기 (변경)
```
변경 전:
  모든 질문 → classify_question(regex) → 매칭 시 템플릿

변경 후:
  is_nudge=True  → classify_question(regex) → 매칭 시 템플릿
  is_nudge=False → category=None → LangGraph LLM fallback
```

## 3. 주요 결정사항

| 결정 | 근거 |
|------|------|
| 수익률은 프론트엔드에서 계산 | API 변경 불필요, normalized_prices 이미 존재 |
| 산점도는 SpreadChart 내 최상단 패널 | 3-패널 구조로 정보량 유지 (scatter + 가격 + z-score) |
| is_nudge=False → regex 스킵 | 사용자 직접 질문에 LLM 자유 응답 보장, 코드 변경 최소화 |
| LLM Classification은 Phase D/E로 이연 | 현재 1개 페이지만 활성, 페이지 라우팅 불필요 |
| 넛지 칩 상시 표시 (조건 제거) | 사용자가 답변 후에도 다른 넛지 질문 쉽게 시도 가능 |

## 4. 컨벤션 체크리스트

### Backend
- [ ] `classify_question()` 호출 조건 변경만 — 함수 자체 수정 없음
- [ ] 기존 테스트 regression 통과
- [ ] API 스키마 변경 없음

### Frontend
- [ ] TypeScript strict 준수
- [ ] `disabled` prop optional 기본값 false
- [ ] tsc --noEmit + vite build 성공
- [ ] Recharts ScatterChart import 패턴 기존과 일관
