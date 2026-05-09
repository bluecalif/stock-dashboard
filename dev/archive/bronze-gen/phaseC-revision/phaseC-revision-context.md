# Phase C-rev: 상관도 페이지 피드백 반영 — Context
> Last Updated: 2026-03-14
> Status: Planning

## 1. 핵심 파일

### Backend — 수정 대상
| 파일 | 수정 내용 |
|------|----------|
| `backend/api/routers/correlation.py` | 응답에 `asset_names` 매핑 추가, spread 응답에 `normalized_prices` 추가 |
| `backend/api/schemas/correlation.py` | `SpreadResponse`에 `normalized_prices` 필드, 기타 응답에 `asset_names` |
| `backend/api/services/analysis/spread_service.py` | `SpreadResult`에 `norm_a_values`, `norm_b_values` 추가 |
| `backend/api/services/chat/chat_service.py` | `status` SSE 이벤트 추가, `is_nudge` 처리 |
| `backend/api/services/llm/hybrid/classifier.py` | 넛지 질문 패턴 보강 |
| `backend/api/schemas/chat.py` | `SendMessageRequest`에 `is_nudge` 필드 |

### Frontend — 수정 대상
| 파일 | 수정 내용 |
|------|----------|
| `frontend/src/pages/CorrelationPage.tsx` | nameMap 생성, 히트맵 셀 클릭, 분포 삭제, 그래프 설명 |
| `frontend/src/components/charts/SpreadChart.tsx` | 2-패널 (가격 오버레이 + z-score) |
| `frontend/src/components/charts/ScatterPlotChart.tsx` | nameMap prop으로 라벨 표시 |
| `frontend/src/components/correlation/CorrelationGroupCard.tsx` | nameMap prop, 페어 선택 UI |
| `frontend/src/components/chat/ChatPanel.tsx` | 타이핑 인디케이터, status 이벤트, is_nudge 전달 |
| `frontend/src/components/chat/NudgeQuestions.tsx` | is_nudge 플래그 전달 |
| `frontend/src/components/chat/MessageBubble.tsx` | 상태 메시지 표시 UI |
| `frontend/src/hooks/useSSE.ts` | `onStatus` 콜백 추가 |
| `frontend/src/api/chat.ts` | `sendMessageSSE`에 `is_nudge` |
| `frontend/src/types/chat.ts` | SSEEvent에 `status` 타입 |

### 참고 파일 (읽기만)
| 파일 | 용도 |
|------|------|
| `backend/db/models.py` | `AssetMaster` 모델 (name 필드 확인) |
| `backend/api/repositories/asset_repo.py` | 자산 목록 조회 |
| `frontend/src/store/chartActionStore.ts` | highlightedPair 상태 |
| `frontend/src/store/chatStore.ts` | 스트리밍 상태 |

## 2. 데이터 인터페이스

### 종목명 매핑
- 입력: `asset_master` 테이블 → `{asset_id: name}` dict
- 출력: 모든 상관도 API 응답에 `asset_names` dict 포함
- Frontend: `assetNameMap: Record<string, string>` 상태

### 정규화 가격
- 입력: `spread_service.compute_spread()` — 이미 `norm_a`, `norm_b` 계산 중
- 출력: `SpreadResponse.normalized_prices.asset_a: number[]`, `.asset_b: number[]` (base=100)
- Frontend: `SpreadChart` 상단 패널에서 2개 LineChart

### 채팅 SSE 이벤트 (신규: `status`)
```
{"type": "status", "data": {"step": "analyzing"|"thinking"|"fetching", "message": "..."}}
```
- 기존 이벤트 순서: `status` → `text_delta`* → `ui_action`* → `done`

### 넛지 질문 플래그
```json
// SendMessageRequest 확장
{"content": "...", "deep_mode": false, "page_context": {...}, "is_nudge": false}
```

## 3. 주요 결정사항

| 결정 | 근거 |
|------|------|
| 종목명은 API 응답에 매핑 dict로 포함 | 프론트에서 별도 조회 최소화, 응답 자체로 완결 |
| 히트맵 셀 클릭 = primary 페어 선택 수단 | 그룹 카드 클릭보다 직관적, 3종목 문제도 해결 |
| 2-패널 차트 (가격 + z-score) | 가격 감각 + 통계적 판단 동시 제공 |
| is_nudge 플래그로 템플릿 응답 보장 | 분류기 패턴 누락 방어 |
| status SSE 이벤트 추가 | 기존 이벤트 타입 확장으로 하위 호환 유지 |
| LangSmith = 환경변수만 (코드 변경 없음) | LangChain 자동 감지 |

## 4. 컨벤션 체크리스트

### Backend
- [ ] API 응답 스키마 Pydantic 정의
- [ ] 기존 테스트 regression 통과
- [ ] SSE 이벤트 하위 호환 (신규 타입 추가, 기존 삭제 없음)
- [ ] `is_nudge` 필드 Optional[bool] = False (하위 호환)

### Frontend
- [ ] TypeScript strict 준수
- [ ] nameMap undefined 안전 처리 (`nameMap?.[id] ?? id`)
- [ ] 차트 반응형 (모바일 세로 스택)
- [ ] tsc --noEmit + vite build 성공
