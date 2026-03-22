# Phase F: Full Agentic Flow — Context
> Last Updated: 2026-03-22
> Status: Complete

## 1. 핵심 파일

### 수정 대상
| 파일 | 용도 | Step |
|------|------|------|
| `backend/api/services/chat/chat_service.py` | 핵심 리팩토링 — agentic flow 통합 | F.6 |
| `frontend/src/components/chat/ChatPanel.tsx` | navigate 핸들러 + follow-up UI | F.7, F.8 |
| `frontend/src/types/chat.ts` | SSEEvent에 follow_up 타입 추가 | F.7 |
| `frontend/src/hooks/useSSE.ts` | follow_up 이벤트 파싱 | F.7 |
| `frontend/src/store/chatStore.ts` | followUpQuestions 상태 | F.7 |

### 신규 생성
| 파일 | 용도 | Step |
|------|------|------|
| `backend/api/services/llm/agentic/__init__.py` | 패키지 초기화 | F.1 |
| `backend/api/services/llm/agentic/schemas.py` | ClassificationResult, CuratedReport, UIActionModel | F.1 |
| `backend/api/services/llm/agentic/knowledge_prompts.py` | Classifier + 4개 Expert 프롬프트 | F.2 |
| `backend/api/services/llm/agentic/classifier.py` | LLM Classifier (Structured Output) | F.3 |
| `backend/api/services/llm/agentic/data_fetcher.py` | Tool 동적 호출 | F.4 |
| `backend/api/services/llm/agentic/reporter.py` | LLM Reporter (Structured Output) | F.5 |

### 재사용 (수정 없음)
| 파일 | 용도 |
|------|------|
| `backend/api/services/llm/tools.py` | 9개 LangChain Tool — DataFetcher에서 직접 호출 |
| `backend/api/services/llm/hybrid/actions.py` | UIAction dataclass + factory helpers |
| `backend/api/services/llm/graph.py` | LangGraph StateGraph — general fallback |
| `backend/api/services/llm/prompts.py` | 기존 시스템 프롬프트 (참조) |
| `backend/api/repositories/asset_repo.py` | get_name_map, get_all — 종목명 매핑 |

### 정리 대상 (F.9)
| 파일 | 변경 내용 |
|------|-----------|
| `backend/api/services/llm/hybrid/classifier.py` | regex classifier — import 제거 후 삭제 또는 보존 |
| `backend/api/services/llm/hybrid/templates.py` | 하드코딩 템플릿 — `get_nudge_questions`만 유지, 나머지 제거 |
| `backend/api/services/llm/hybrid/context.py` | PageContext — agentic flow에서도 사용 가능, 유지 |

## 2. 데이터 인터페이스

### Classifier (입력 → 출력)
```
입력:
  - question: str (사용자 질문)
  - page_id: str (현재 페이지: home/prices/correlation/indicators/strategy)
  - asset_ids: list[str] (페이지에서 선택된 자산)
  - params: dict (페이지별 파라미터: window, forward_days 등)

출력: ClassificationResult
  - target_page: str
  - should_navigate: bool (target_page ≠ 현재 page_id)
  - category: str (10개: correlation_explain, similar_assets, spread_analysis,
                    indicator_explain, signal_accuracy, indicator_compare,
                    strategy_explain, strategy_backtest, strategy_compare, general)
  - required_tools: list[str] (9개 tool 중 선택)
  - asset_ids: list[str] (질문에서 추출한 자산 ID)
  - params: dict (tool 호출에 필요한 파라미터)
  - confidence: float (0.0~1.0)
```

### DataFetcher (입력 → 출력)
```
입력: ClassificationResult
출력: dict[str, Any]
  - 각 tool_name → JSON parsed 결과
  - name_map: dict[str, str] (asset_id → 종목명)
```

### Reporter (입력 → 출력)
```
입력:
  - category: str
  - tool_results: dict[str, Any]
  - page_id: str (target_page)
  - question: str
  - deep_mode: bool

출력: CuratedReport
  - summary: str (1-2줄 핵심 요약)
  - analysis: str (마크다운 상세 분석)
  - verdict: str (판단 근거 결론)
  - ui_actions: list[UIActionModel]
  - follow_up_questions: list[str] (3개)
```

### SSE 이벤트 흐름 (chat_service → 프론트엔드)
```
1. {"type": "status", "data": {"step": "analyzing", "message": "질문 분석 중..."}}
2. {"type": "ui_action", "action": "navigate", "payload": {"path": "/correlation"}}  ← 네비게이션 시
3. {"type": "status", "data": {"step": "fetching", "message": "데이터 조회 중..."}}
4. {"type": "status", "data": {"step": "analyzing", "message": "분석 보고서 생성 중..."}}
5. {"type": "text_delta", "content": "## 요약\n..."} (청크 반복)
6. {"type": "ui_action", "action": "highlight_pair", "payload": {...}}  ← Reporter 판단
7. {"type": "follow_up", "questions": ["질문1", "질문2", "질문3"]}  ← 신규 이벤트
8. {"type": "done"}
```

## 3. 주요 결정사항

| 항목 | 결정 | 근거 |
|------|------|------|
| LLM 호출 횟수 | 최대 2회 (Classifier + Reporter) | 다단계 에이전트 대비 레이턴시/비용 최소화 |
| Classifier 모델 | gpt-5-mini (reasoning) 유지 | 질문 의도 파악에 chain-of-thought 유효. temperature 미지원 주의 |
| Reporter 모델 | gpt-4.1-mini (non-reasoning) 분리 | JSON 리포트에 reasoning 불필요. 34.8s → 5.8s (6배 개선) |
| regex classifier | 제거 (LLM 완전 대체) | 확장성 + 페이지 간 라우팅 가능 |
| 하드코딩 템플릿 | 제거 (Reporter 대체) | 자연스러운 분석 + 동적 follow-up |
| 자동 네비게이션 | 즉시 이동 (확인 없음) | Agentic AI UX 극대화 |
| is_nudge 파라미터 | 시그니처 유지, 내부 무시 | 프론트/백 배포 시점 불일치 방지 |
| 기존 LangGraph | general fallback으로 유지 | 분류 실패/일반 대화 처리 |
| UIAction 검증 | Literal 타입 + Pydantic 검증 | LLM hallucination 방지 |
| 기존 넛지 질문 | 정적 넛지 유지 (초기 로드) + 동적 follow-up 추가 | 첫 질문은 정적, 이후는 동적 |
| hybrid/context.py | 유지 | PageContext 구조는 agentic flow에서도 사용 |
| reasoning 모델 호환 | gpt-5-mini/nano는 temperature, max_tokens 미지원 | langchain 400→자동재시도로 "느려짐"으로 나타남. max_completion_tokens 사용 |
| LLM timeout/retry | 모든 ChatOpenAI에 max_retries=2~3, request_timeout=30~60s 명시 | 기본값의 과도한 재시도 방지 |

## 4. 컨벤션 체크리스트

### 이 Phase에 적용되는 규칙
- [x] Pydantic v2 스키마 (ClassificationResult, CuratedReport)
- [x] OpenAI JSON mode (with_structured_output → response_format=json_object 전환)
- [x] SSE 이벤트 포맷 일관성 (text_delta, ui_action, status, done + follow_up 추가)
- [x] 한국어 응답 (Reporter 프롬프트에 명시)
- [x] Router-Service-Repository 패턴 유지 (chat_service.py → agentic 모듈)
- [x] 기존 API 하위호환 (is_nudge 파라미터 유지)
- [x] 기존 테스트 보호 (hybrid 코드 단계적 정리)
- [x] 면책조항 포함 (Reporter 프롬프트)
- [x] 종목 코드 → 종목명 표시 (DataFetcher에서 name_map 포함)
- [x] E2E 통합 검증 (F.10) — 프로덕션 배포 + E2E 검증 완료

### 성능 최적화 관련 변경 파일 (Post-Phase)
| 파일 | 변경 내용 | 커밋 |
|------|-----------|------|
| `backend/config/settings.py` | `llm_report_model` 설정 추가 | `ec2995b` |
| `backend/api/services/llm/agentic/reporter.py` | gpt-4.1-mini 분리 + temperature=0 복원 | `ec2995b` |
| `backend/api/services/llm/agentic/classifier.py` | temperature 제거, timeout=30s, retries=2 | `ec2995b` |
| `backend/api/services/llm/graph.py` | timeout=60s, retries=2 | `ec2995b` |
| `backend/api/services/chat/summarizer.py` | gpt-5-nano temperature=0 제거 | `ec2995b` |
| `backend/.env.example` | LLM_REPORT_MODEL 추가 | `ec2995b` |
| `backend/tests/unit/test_agentic_reporter.py` | 단일 모델 테스트로 변경 | `ec2995b` |

### 신규 컨벤션
- **agentic 패키지 구조**: `backend/api/services/llm/agentic/` 하위에 모듈 배치
- **JSON mode**: `response_format=json_object` + 수동 파싱 (with_structured_output 프로덕션 실패로 전환)
- **confidence threshold**: 0.5 미만 시 LangGraph fallback
- **SSE follow_up 이벤트**: `{"type": "follow_up", "questions": [...]}`
