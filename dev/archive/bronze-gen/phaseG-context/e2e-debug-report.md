# E2E 디버깅 리포트 — indicator_accuracy 이슈

> 목적: `analyze_indicators` → Reporter → 브라우저 전체 플로우에서 "성공률 산출 불가" 버그의 근본 원인 추적

---

## 어젠다 4: server multiplication ✅ DONE
**목표**: 서버 환경 표준화 — 중복 서버 방지 및 E2E 테스트용 서버 관리

- [x] 현재 떠있는 서버 프로세스 전수 확인 (포트, PID)
  - port 8000에 PID 3개 (23268, 6180, 8712) 동시 LISTENING → 2개는 ghost
- [x] 중복 서버 정리 → 전부 kill 후 단일 서버 재시작
- [x] E2E 테스트 전 서버 상태 확인 절차 수립
- [x] 단일 서버 재시작 + 로그 확인 검증 → 성공
- **교훈**: 서버 시작 전 `netstat -ano | grep :8000` + `tasklist` 확인 필수. 중복 서버 시 OS가 라운드로빈으로 요청을 분배 → 로그가 다른 프로세스로 갈 수 있음
- **절차**: `taskkill` → `netstat` 확인 → 서버 시작 → `tail` 로그 확인
- **결과**: 해결 완료

---

## 어젠다 3: bash server log check ✅ DONE
**목표**: 올바른 로그 확인 방법론 정립 (교훈 포함)

- [x] uvicorn 로그 출력 경로 확인
  - uvicorn `--log-level debug`는 **uvicorn 자체 로거만** 영향
  - 앱 코드의 `logging.getLogger(__name__)`은 **Python 루트 로거**를 따름
  - 루트 로거 기본 레벨 = WARNING → 앱 INFO/DEBUG 로그가 전부 무시됨
- [x] **근본 원인**: `api/main.py`에 `logging.basicConfig()` 호출이 없었음
- [x] **수정**: `logging.basicConfig(level=LOG_LEVEL)` 추가 + `LOG_LEVEL` 환경변수 지원
- [x] Git Bash + Windows 로그 캡처: `> /tmp/file.log 2>&1 &` (stdout+stderr 합침)
- **교훈**:
  1. `uvicorn --log-level`과 앱 로거 레벨은 별개
  2. `logging.basicConfig()` 없으면 앱 로그 안 찍힘 (Python 기본 WARNING)
  3. 로그 리다이렉트 시 반드시 `2>&1`로 stderr 포함
- **결과**: `main.py`에 `logging.basicConfig()` 추가하여 해결

---

## 어젠다 2: logging addition issue ✅ DONE
**목표**: 추가한 디버그 로깅이 실제 동작하는지 확인하고, agentic flow의 병목점 파악

- [x] reporter.py — 3개 debug 로그 동작 확인
  - `system_prompt (first 500)`: INDICATORS_EXPERT_PROMPT 사용 확인 ✅
  - `user_msg (first 1000)`: indicator_accuracy JSON 포함 확인 ✅
  - `raw response (first 500)`: LLM 응답 JSON 확인 ✅
- [x] data_fetcher.py — `indicator_accuracy found in analyze_indicators: 2 entries` ✅
- [x] chat_service.py — `Agentic flow: use_agentic=True, category=signal_accuracy` ✅
- [x] 로그 레벨: `logging.basicConfig()` 추가 후 DEBUG 출력 정상 확인
- **병목점**: Reporter LLM 호출 22:26:12 → 응답 22:26:33 (약 22초 소요)
- **결과**: 모든 로그 정상 동작 확인

---

## 어젠다 1: accuracy call issue ✅ DONE
**목표**: 브라우저와 API 응답에서 indicator_accuracy 데이터가 정상 전달되는지 확인

- [x] analyze_indicators 툴 → indicator_accuracy 2개 엔트리 (rsi_14, macd) 반환 확인
- [x] DataFetcher → Reporter: user_msg에 indicator_accuracy JSON 포함 확인
- [x] Reporter: MACD 매수 성공률 73.91% 정상 응답 (buy_success_rate=0.7391)
- [x] 브라우저: 스크린샷에서 MACD 성공률 표시 확인

### 근본 원인 분석
**이전 버그("성공률 산출 불가")의 원인**:
1. `analyze_indicators` 툴에 `indicator_accuracy` 필드가 **없었음** (d834c97에서 추가)
2. 데이터에 `signal_accuracy`만 존재 → 전략(momentum/trend/mean_reversion)의 신호 데이터 = 0건
3. LLM이 `signal_accuracy.insufficient_data=true`만 보고 "성공률 산출 불가" 응답
4. d834c97 커밋에서 `indicator_accuracy` (RSI/MACD 개별 지표 성공률) 추가 후 정상 동작

### E2E 플로우 타임라인 (로그 기반)
```
22:25:59.184  Classifier: category=signal_accuracy, confidence=0.90, tools=[analyze_indicators]
22:26:01.807  chat_service: use_agentic=True
22:26:09.920  DataFetcher: analyze_indicators 성공 (2211 chars), indicator_accuracy 2 entries
22:26:11.190  Reporter: system_prompt (INDICATORS_EXPERT_PROMPT) + user_msg (indicator_accuracy 포함)
22:26:12.372  OpenAI API 호출 (gpt-5-mini)
22:26:33.910  Reporter: 응답 수신, MACD 매수 73.91% 포함
```

- **결과**: d834c97 커밋으로 이미 수정 완료. 현재 정상 동작 확인.

---

## 코드 변경 요약

| 파일 | 변경 내용 | 유형 |
|------|-----------|------|
| `api/main.py` | `logging.basicConfig()` + `LOG_LEVEL` 환경변수 | 버그 수정 (로그 미출력) |
| `api/services/llm/agentic/reporter.py` | system_prompt, user_msg, raw response DEBUG 로그 3개 | 디버깅 |
| `api/services/llm/agentic/data_fetcher.py` | indicator_accuracy 키 존재 INFO 로그 1개 | 디버깅 |
| `api/services/chat/chat_service.py` | agentic flow 진입 INFO 로그 1개 | 디버깅 |

## 후속 조치
- [ ] 디버그 로그를 프로덕션에서 유지할지 결정 (현재 DEBUG 레벨이므로 기본 실행 시 안 보임)
- [ ] Reporter LLM 응답 시간 22초 — 성능 최적화 검토 필요 여부
