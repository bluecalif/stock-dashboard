# Silver rev1 — Draft 분석 + 인터뷰 질문 (다음 세션 재개용)

> Generated: 2026-05-06
> 역할: `docs/draft-rev1.md`에 대한 비판적 분석 + 누락점 정리 + 인터뷰 질문 캡슐.
> 다음 세션은 이 문서의 **Part D 인터뷰 질문**부터 답변을 받는 흐름으로 재개한다.

## Part A — 현재 상황 요약 (Bronze → Silver 갭)

| 항목 | Bronze (현재) | Silver rev1 (draft) | 갭 |
|---|---|---|---|
| 자산 수 | 7개 (KS200/005930/000660/SOXL/BTC/GC=F/SI=F) | 13개 + WBI synthetic | **+8개 신규 + benchmark** |
| 페이지 IA | 5탭 (Dashboard/Price/Correlation/Indicators/Strategy) | 1메인 (적립식 3탭) + 보조 | **IA 재편** |
| 화폐 처리 | 단일 통화 가정 (FX 데이터 없음) | "매 날짜 환율" 기반 KRW 환산 | **FX 인프라 부재** |
| 시뮬레이션 엔진 | 백테스트 (시그널 기반) | 적립식 replay + 조건전략 + 포트폴리오 | **신규 엔진 필요** |
| Bronze 완료도 | Phase F까지 198 commits, 874 tests, 운영중 | – | **운영 중에 IA를 갈아끼우는 작업** |

**핵심 판단**: Silver는 "Bronze의 폴리시"가 아니라 "다른 제품"이다. 데이터 파이프라인 확장 + 시뮬레이션 엔진 신규 + IA 재편이 동시에 필요하다.

## Part B — 비판적이지만 건설적 관점에서의 7대 허들

### B-1. 데이터 확장 (가장 큰 인프라 허들)
- `backend/collector/fdr_client.py:14`의 `SYMBOL_MAP`은 7종 고정. QQQ/SPY/SCHD/JEPY/TLT/NVDA/GOOGL/TSLA 8종 추가 필요.
- `JEPY`는 모호: JPMorgan **JEPI** (Equity Premium Income), YieldMax **JEPY** (S&P 500 0DTE), Defiance **JEPI** 변형 등 혼동 위험. 종목코드 확정 필요.
- 10년치 일봉을 FDR free tier가 모두 제공하는지(특히 SCHD/JEPY 출시일) 확인 필요. JEPY는 신규 ETF라 10년 history 자체가 없을 수도 있음.

### B-2. WBI synthetic 정의 (수식 미확정)
- "연 20% 복리"를 일별 수익률로 어떻게 변환할지 미정. 후보:
  - (a) 거래일 기준 등비: `(1.20)^(1/252) - 1 = 0.0727%/일` (smooth curve, 변동성 0)
  - (b) 캘린더 일 기준: `(1.20)^(1/365) - 1`
  - (c) 매월 1.5309% 일괄 적용 (월별 stepwise)
- 변동성 0인 직선 곡선이 차트에서 "왠지 사기 같다"는 감각적 문제도 고려 대상.

### B-3. 환율 처리 (인프라 부재)
- 현재 repo에 FX 시계열이 없음. USD/KRW 일봉 10년 별도 수집·저장 필요.
- "매 날짜 환율" 적용 위치가 모호:
  - 적립일에 KRW→USD 환산해 fractional shares 매수
  - 평가시점에는 보유 USD 자산을 그날 환율로 KRW 환산
  - **누적 자산가치 곡선**의 매일 KRW 평가 비용(O(N×days)) — 캐시 전략 필요
- 환차익/환손실이 사용자 체감 손실에 합쳐져 노출되는데, "20% 하락" 같은 조건 트리거는 USD 기준인지 KRW 기준인지?

### B-4. 거래일/캘린더 정렬
- KOSPI200(KRX 캘린더)과 QQQ/SPY(NYSE 캘린더)는 휴장일이 다름. 한 차트에 같이 그릴 때:
  - forward-fill? 영업일 합집합? 합집합 후 빈 곳은 직선?
- "매월 첫 거래일" 정의도 KRX 기준인지 NYSE 기준인지(자산별로 다를 수밖에 없음).

### B-5. 전략 정의의 미세 모호성 (Tab B)
- 전략 A 급등 조건 "3개월 내 20% 상승": **60거래일 전 대비** 종가 ≥ 20%↑인가? 아니면 3개월 윈도우 안의 어느 시점들 사이의 max-min ratio?
- "1년 내 급락 없으면 12월 마지막 거래일" — *어느* 12월? 매도일 +365일 안의 12월? 매도 다음 해 12월? **여러 해석 가능**.
- "같은 해에 1회만 실행" — 매도·재매수 페어 1쌍 / 매도 1회 / 재매수 1회 어떤 기준?
- 초기 보유분이 없는 적립식 시작 직후(예: 1개월차)에는 "보유수량의 30%"가 1주만 매도. 정상 동작인가, 또는 grace period?

### B-6. MDD 정의
- "연도별 MDD 중 최악" — 기준이 두 가지로 갈림:
  - **누적 자산가치(KRW 평가금액)** 기준: 적립금 유입과 가격 변동 모두 반영
  - **누적 수익률** 기준: 문서 예시 "40%→20%" 표현이 가리키는 방향
- 두 정의의 결과는 다르다. 적립식은 매월 새 자금이 들어와 분모가 커지므로, 같은 가격 폭락이라도 두 metric의 폭이 다르다.

### B-7. 운영/배포 충돌
- Bronze가 운영 중. Silver 라우트로 갈아끼울 때:
  - `/`, `/prices`, `/correlation`을 redirect로 막을지, 별도 build로 분리할지.
  - StrategyPage drop은 **DB 테이블도 drop**인지(backtest_run/equity_curve/trade_log) 또는 **테이블 유지+페이지만 제거**인지.
  - Agentic AI(Phase F)가 기존 dashboard/price/correlation/strategy API를 tool로 사용 중. Silver에서 라우트를 막으면 LLM tool도 같이 정리해야 함 (A-004 교훈).

## Part C — 누락점 정리 (Gap Map)

### C-1. 데이터/스키마
- [ ] 신규 자산 8종 종목코드 + 한글명 + 카테고리 + 통화 매핑표
- [ ] JEPY 정확한 ticker 확정
- [ ] USD/KRW 일봉 수집 정책 (FDR `USD/KRW`)
- [ ] WBI 일별 수익률 산식 확정
- [ ] asset_master에 currency / fractional_allowed / dividend_yield 컬럼 필요 여부
- [ ] 배당/이자 재투자: 실제 배당락 데이터 사용 vs 공시 배당률 가정

### C-2. 시뮬레이션 엔진
- [ ] 적립식 replay 모듈 신규 설계 (research_engine 안에?)
- [ ] 환율 환산 시점 정책
- [ ] 다중 캘린더 정렬 정책
- [ ] 부분 매수/매도 fractional 정밀도 (소수점 몇 자리?)
- [ ] 전략 A/B 모호성 5건 (B-5 참고)
- [ ] 포트폴리오 연 1회 리밸런싱 비용 (시뮬상 0)
- [ ] 60% 슬롯 내부가 멀티자산일 때(예: SEC/SKH 1:1) 내부 비중 유지 규칙

### C-3. UI/IA
- [ ] 사이드바 폐기 후 nav 위치 (top horizontal 가정?)
- [ ] Tab A 자산 추가 UI (체크박스 vs dropdown vs drawer)
- [ ] Tab A 최대 동시 비교 자산 수
- [ ] Tab A에서 NVDA/GOOGL/TSLA/SEC/SKH/BTC/TLT 비교 가능 여부 (draft 8.2가 6종으로 제한해 보임)
- [ ] 카드형 vs step형 결정 시점 (draft 6.2: "시안 후 결정")
- [ ] 신호 상세 페이지의 IA (draft 12.2: "후속 논의로 확정")
- [ ] 모바일 대응 범위 (rev1 포함?)
- [ ] 한국어 UI에서 USD 자산 가격 표기 규칙

### C-4. 신호/지표
- [ ] 신호 카드 내용 (현재 시점 RSI 값? 최근 시그널 이벤트? 추세 상태?)
- [ ] 신호 빈도 기준 (silver-draft.md의 "3회/년" 가이드는 rev1에서 사라졌는데 유지/폐기?)
- [ ] 신호 자산 8종에 BTC/TLT/SCHD/JEPY/WBI 미포함 — 의도적인가?
- [ ] 적립식 메인 안의 "지표 요약 카드"가 탭별로 다른가, 동일한가?

### C-5. AI/Chat
- [ ] Silver에서 chat 기능 유지/축소/제외?
- [ ] 적립식 시뮬레이션 결과를 LLM이 해석하는 카드 도입?
- [ ] StrategyPage drop 시 Agentic tool에서 strategy 분류·리포트 분기 정리

### C-6. 인증/저장
- [ ] 적립식 시뮬레이션 결과 저장 (사용자별 history)?
- [ ] 비로그인 접근 정책 (Bronze는 일부 페이지만 인증)
- [ ] 사용자 프로필 페이지 처리

### C-7. 운영/배포
- [ ] 데이터 backfill 순서 (먼저 backfill 완료 후 Silver 노출 vs 점진)
- [ ] Bronze→Silver 전환 방식 (빅뱅 / feature flag / blue-green)
- [ ] 레거시 페이지 redirect 목적지
- [ ] 테이블 drop vs 유지 (StrategyPage 드랍 시)
- [ ] 데이터 정합성 알림(alerting.py) 신규 자산에 확장

### C-8. 검증
- [ ] 적립식 계산을 외부 사이트(Portfoliovisualizer 등) 결과와 cross-check
- [ ] 1차 기준 자산(QQQ 10년 적립)을 known-good 결과 fixture로
- [ ] 사용자 검증(초보 5명) 일정/플랜

## Part D — 인터뷰 질문 (다음 세션 시작점)

> 답변은 클러스터 단위로 받아도 됨. 각 질문에 옵션이 있으면 옵션 번호로, 없으면 자유 서술.
> 우선순위: Q1~Q3가 데이터·환율·WBI라 가장 시급. 답변되면 인프라 허들이 풀린다.

### Q1. 자산/데이터 확정
1. **JEPY**의 정확한 ticker는? (예: `JEPI` JPMorgan / `JEPY` YieldMax / 기타) FDR에서 다운받아 출시일과 시계열 확인.
2. SCHD/JEPY/TLT의 history가 10년 미만인 경우 처리: (a) 가능한 만큼만 (b) WBI 식 대체값 padding (c) Tab A에서 제외
3. **USD/KRW 환율 데이터**: FDR `USD/KRW` 일봉으로 수집해 별도 테이블(`fx_daily`)에 저장하는 방향 OK?
4. 배당/이자 처리: (a) 실제 배당락 일자 데이터로 정확 재투자 (b) 공시 배당률 균등 분할 가정 — 어느 쪽?

### Q2. WBI 산식 확정
5. WBI 일별 수익률: (a) 거래일 등비 `(1.20)^(1/252)-1` (b) 캘린더 등비 (c) 매월 stepwise (d) 기타
6. WBI는 KRW 자산? USD 자산? (환율 영향 없음 가정인가?)

### Q3. 환율/통화 정책
7. 적립일 환산: KRW 100만원을 USD 자산 매수 시 그날 종가 환율로 USD 변환 후 fractional shares 매수 — OK?
8. 누적 자산가치를 KRW로 그릴 때, 매일 보유 USD 평가액을 그날 환율로 환산 — OK? 성능 우려 있어 일별이 아닌 월별 환산도 옵션.
9. Tab B 전략 A의 "20% 상승/10% 하락" 트리거 기준은 (a) 현지통화 가격 기준 (b) KRW 환산 기준?

### Q4. 전략 A/B 모호성 해소
10. 전략 A 급등 조건 "3개월 내 20% 상승" = `오늘종가 / 60거래일 전 종가 ≥ 1.20` 으로 단순화해도 OK?
11. 전략 A "1년 내 급락 없으면 12월 마지막 거래일" — 어느 해의 12월? (a) 매도일이 속한 해 (b) 매도일 +1년 안의 12월 (c) 매도 다음 해 12월
12. 전략 A "같은 해에 1회만 실행"의 단위 = (a) 매도·재매수 페어 1쌍 (b) 매도 액션 1회 (c) 재매수 액션 1회
13. 전략 시작 직후(보유수량이 적은 시기) 매도 30% 트리거는 그대로 실행? 아니면 첫 N개월 grace period?

### Q5. MDD 정의 확정
14. "연도 기준 최대 손실폭"의 계산 기준: (a) 누적 자산가치 KRW (b) 누적 수익률(%) (c) 두 가지 모두 노출
15. "연도"의 단위: (a) 캘린더 연도 (Jan-Dec) (b) 12개월 rolling

### Q6. UI/IA 확정
16. 좌측 사이드바 폐기 후 메인 nav 위치: (a) top horizontal (b) hidden + drawer (c) 기타
17. Tab A에서 비교 가능한 자산 universe = (a) draft 8.2의 6종 한정 (QQQ/SPY/KS200/SCHD/JEPY/WBI) (b) 7.1의 13종 전체 (c) 기타 조합
18. Tab A 자산 추가 UI: (a) 체크박스 multi-select (b) "+" 버튼 + 자산 picker (c) 기타
19. Silver에서 chat/AI 기능: (a) 그대로 유지 (b) 적립식 결과 해석 카드로 통합 (c) rev1에서는 제외
20. 모바일 대응: (a) rev1 필수 (b) rev2로 미루기

### Q7. 신호/지표 범위
21. 메인 적립식 탭 안의 "지표 요약 카드" — 어떤 정보? (a) 현재 RSI/MACD/ATR 값 + 상태 라벨 (b) 최근 발생 시그널 timeline (c) 기타
22. 신호 자산 8종(BTC/TLT/SCHD/JEPY/WBI 제외)이 의도적인지, 또는 누락인지 확인.
23. 신호 상세 페이지 — 기존 IndicatorSignalPage를 (a) 단순 단순화 (b) 전면 재구성 (c) 신규 페이지 작성

### Q8. 운영/배포 정책
24. Bronze → Silver 전환 방식: (a) 새 도메인/route 추가하고 점진 (b) 빅뱅 교체 (c) feature flag
25. 레거시 페이지(/, /prices, /correlation, /strategy) 처리: (a) 메인 적립식으로 redirect (b) "Silver로 이동" 안내 페이지 (c) 404
26. StrategyPage drop 시 백엔드: (a) DB 테이블도 drop (b) API/테이블 유지하고 라우트만 차단 (c) Agentic tool에서만 제거
27. 데이터 backfill 순서: (a) 신규 8종 + 환율을 모두 backfill 완료 후 Silver 페이지 노출 (b) 페이지 먼저 띄우고 데이터 도착 시 노출

## Part E — 다음 단계 (Silver Masterplan 목차 후보)

Q1~Q8 답변이 모이면 아래 구조로 마스터플랜 작성:

```
1. 제품 정의 & 성공 기준 (KPI)
2. 자산/데이터 확정표
3. 시뮬레이션 엔진 명세 (수식 포함)
4. IA & 화면 명세 (와이어프레임 수준)
5. 백엔드 변경 명세 (스키마, API, 컬렉터)
6. 프론트엔드 변경 명세 (라우트, 컴포넌트)
7. 데이터 backfill 플랜
8. Phase 분할 (Bronze 운영 영향 최소화 순서)
9. 테스트/검증 전략
10. 배포/롤아웃 플랜
11. 리스크 & 미해결 후속 과제
```

## Part F — 현재 코드 기준 사실 메모 (재탐색 불필요용)

- 현재 FDR 자산 7종: `KS200`, `005930`, `000660`, `SOXL`, `BTC` (BTC/KRW), `GC=F`, `SI=F` — `backend/collector/fdr_client.py:14`
- 현재 프론트 페이지 9개: Factor, Dashboard, Price, Login, Signup, Strategy, IndicatorSignal, Correlation, Signal — `frontend/src/pages/`
- 현재 API 라우터 13개: assets, prices, factors, signals, backtests, dashboard, health, correlation, chat, profile, analysis, auth — `backend/api/routers/`
- DB 마이그레이션 6단계 완료 (initial 8tables, backtest 컬럼 추가, auth, chat, profile, conversation_summaries)
- Phase F 완료 — Reporter LLM 분리 (gpt-4.1-mini), Cache Warmup 구현
- 환율 데이터 없음 (FX 인프라 부재)
- Bronze 운영중, Phase F까지 완료된 상태
