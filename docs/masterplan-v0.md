# Masterplan v0 - Stock Dashboard

## 1. 프로젝트 요약
- 목표: 7개 자산(KOSPI200, 삼성전자, SK하이닉스, SOXL, BTC, Gold, Silver)의 일봉 데이터 수집/저장/분석/시각화를 MVP로 구축한다.
- 운영 기준: Windows 단일 호스트(수집기/API/대시보드), PostgreSQL은 Railway 사용.
- 핵심 원칙: 빠른 가동(MVP) + 재현 가능한 분석 파이프라인 + 단계적 고도화.

## 2. 현재 상태 진단 (코드베이스 리뷰)
- 저장소에는 앱 코드 없이 문서만 존재한다.
- 확인 파일:
  - `docs/guide_financereader.md`
  - `docs/plan_draft.md`
- 결론: 본 문서는 구현 가이드가 아닌 "구현 명세서"로 작성하며, 이후 코드 생성의 단일 기준으로 사용한다.

## 3. 범위 정의
### 3.1 인스코프 (v0)
- 데이터 수집:
  - 전 자산(7종): FinanceDataReader(FDR) 단일 소스
  - 배포 직전 단계(v0.9+)에서 한국투자증권(Hantoo) REST API를 fallback으로 추가
- 저장:
  - 표준화 OHLCV 스키마로 PostgreSQL 적재
- 분석:
  - 팩터 생성
  - 전략 3종(모멘텀/추세/평균회귀)
  - 백테스트 및 성과지표
- 제공:
  - 조회 API
  - 기본 대시보드(가격/수익률/상관/전략 성과)

### 3.2 아웃오브스코프 (v0)
- 실거래 자동주문
- 딥러닝 기반 예측 모델
- 멀티 리전/고가용성 클러스터

## 4. 아키텍처
- `collector` (Python): FDR 기반 REST 수집, 정합성 검증, UPSERT
- `research_engine` (Python): 팩터, 전략 신호, 백테스트, 리포트
- `api` (FastAPI): 데이터/분석 결과 조회
- `dashboard` (React + Recharts): 시각화 SPA, API 소비
- `scheduler` (Windows Task Scheduler): 배치 실행
- `database` (Railway PostgreSQL): 영속 저장, Alembic 마이그레이션

데이터 흐름:
1. 스케줄러가 수집 작업 실행
2. 수집 데이터 표준화 및 저장
3. 분석 배치가 팩터/신호/백테스트 계산
4. API가 저장 결과 제공
5. 대시보드가 API를 렌더링

## 5. 데이터 소스 정책
### 5.1 자산별 소스 우선순위
- KOSPI200: `KS200` (FDR)
- 삼성전자: `005930` (FDR 1순위, Hantoo fallback v0.9+)
- SK하이닉스: `000660` (FDR 1순위, Hantoo fallback v0.9+)
- SOXL: `SOXL` (FDR)
- BTC: `BTC/KRW` 기본, 실패 시 `BTC/USD`
- Gold: `GC=F`
- Silver: `SI=F`

### 5.2 표준 데이터 스키마
- 공통 필드: `asset_id`, `date`, `open`, `high`, `low`, `close`, `volume`, `source`, `ingested_at`
- 기본 규칙:
  - 고가/저가 역전 금지
  - 음수 가격 금지
  - 동일 키 중복 시 최신 ingest 우선

## 6. 데이터베이스 설계
### 6.1 `asset_master`
- `asset_id` (PK)
- `name`
- `category` (`stock/index/etf/crypto/commodity`)
- `source_priority` (JSON)
- `is_active`

### 6.2 `price_daily`
- `asset_id` (FK)
- `date`
- `open`, `high`, `low`, `close`, `volume`
- `source`
- `ingested_at`
- PK: `(asset_id, date, source)`
- 인덱스: `(asset_id, date DESC)`, `(date)`

### 6.3 `factor_daily`
- `asset_id`, `date`, `factor_name`, `value`, `version`
- PK: `(asset_id, date, factor_name, version)`

### 6.4 `signal_daily`
- `asset_id`, `date`, `strategy_id`, `signal`, `score`, `action`, `meta_json`

### 6.5 `backtest_run`
- `run_id` (PK)
- `strategy_id`
- `config_json`
- `started_at`, `ended_at`
- `status`

### 6.6 `backtest_equity_curve`
- `run_id`, `date`, `equity`, `drawdown`

### 6.7 `backtest_trade_log`
- `run_id`, `asset_id`, `entry_date`, `exit_date`, `side`, `pnl`, `cost`

### 6.8 `job_run`
- `job_id` (PK)
- `job_name`
- `started_at`, `ended_at`
- `status`
- `error_message`

## 7. 분석 모듈 상세
## 7.1 전처리
- 캘린더 정렬(영업일 기준)
- 결측 처리 정책(허용 임계치 초과 시 실패)
- 이상치 플래그 생성

## 7.2 팩터 생성
- 수익률: `ret_1d`, `ret_5d`, `ret_20d`, `ret_63d`
- 추세: `sma_20`, `sma_60`, `sma_120`, `ema_12`, `ema_26`, `macd`
- 모멘텀: `roc`, `rsi_14`
- 변동성: `vol_20`, `atr_14`
- 거래량: `vol_zscore_20`

## 7.3 전략 엔진 (MVP 3종)
- 모멘텀 전략:
  - 진입: `ret_63d > threshold` 및 `vol_20 < cap`
  - 청산: 모멘텀 약화 또는 변동성 초과
- 추세 전략:
  - 진입: `sma_20 > sma_60` (골든크로스)
  - 청산: `sma_20 < sma_60`
- 평균회귀 전략:
  - 진입: 가격 z-score 하단 밴드 이탈 후 복귀 시
  - 청산: 평균 회귀 달성 또는 손절

공통 체결 규칙:
- 신호 발생 다음 거래일 시가 체결
- 수수료/슬리피지 반영
- 포지션: 기본 1배, 현금 비중 허용

## 7.4 백테스트
- 모드: 단일 자산 / 다중 자산
- 분할: 워크포워드 구간 지원
- 산출물:
  - 에쿼티 커브
  - 트레이드 로그
  - 성과 요약

## 7.5 성과 평가 지표
- 수익: 누적수익률, CAGR
- 리스크: MDD, 변동성
- 위험조정수익: Sharpe, Sortino, Calmar
- 운용지표: 승률, Turnover
- 벤치마크: Buy&Hold 대비 초과성과

## 8. API 명세 (v1)
- `GET /v1/assets`
- `GET /v1/prices/daily?asset_id=&from=&to=`
- `GET /v1/factors?asset_id=&from=&to=`
- `GET /v1/signals?asset_id=&asof=`
- `POST /v1/backtests/run`
- `GET /v1/backtests/{run_id}`
- `GET /v1/backtests/{run_id}/equity`
- `GET /v1/backtests/{run_id}/trades`
- `GET /v1/health`

응답 원칙:
- UTC 타임스탬프
- 숫자 타입 일관성
- 오류 코드 표준화(`4xx` 입력 오류, `5xx` 서버 오류)

## 9. 운영 및 배치
- 스케줄:
  - 일일 수집 배치: 장 마감 후 실행
  - 분석 배치: 수집 성공 시 후속 실행
- 실패 복구:
  - FDR 지수 백오프 재시도
  - 자산 단위 지연 처리
  - 재처리 가능한 idempotent UPSERT
  - 지속 실패 시 배치 부분 성공 허용 + 알림 발송
- 관측성:
  - JSON 로그
  - 작업별 성공/실패율
  - 실패 알림(Discord Webhook)

## 10. 보안 및 설정
- 비밀값: 환경변수로만 관리
- DB TLS 연결 강제
- API 키/토큰은 코드 하드코딩 금지
- 로컬 로그에 민감정보 마스킹

## 11. 테스트 전략
### 11.1 단위 테스트
- 심볼 매핑
- 전처리/결측 처리
- 팩터 계산 정확성
- 전략 신호 경계값

### 11.2 통합 테스트
- `collector -> DB -> research_engine -> API` E2E
- 백테스트 요청/결과 조회 일관성

### 11.3 회귀 테스트
- 고정 샘플 데이터셋의 성과 스냅샷 비교

### 11.4 수용 기준
- 7개 자산 최근 1년 데이터 조회 성공
- 전략 3종 백테스트 성공
- 대시보드 핵심 화면 렌더 성공
- 배치 실패 알림 수신 확인

## 12. 마일스톤 (5주)
- 1주차: 프로젝트 골격, DB 스키마, FDR 수집 기본
- 2주차: 수집기 안정화, 정합성/복구
- 3주차: 팩터/전략 엔진
- 4주차: 백테스트/API/대시보드
- 5주차: Hantoo fallback 통합, 통합테스트, 운영문서, 배포

## 13. 리스크 및 대응
- FDR 단일 소스 의존:
  - 리스크: FDR 장애 시 전 자산 수집 중단
  - 대응: 배포 직전 Hantoo REST API를 국내주식(005930, 000660) fallback으로 추가
  - 모니터링: FDR 실패율 추적, 임계치 초과 시 알림
- 데이터 소스 차이:
  - `source` 추적 및 품질 리포트 분리
- 단일 Windows 호스트 장애:
  - 주기 백업 및 재기동 스크립트 준비

## 14. 향후 확장 (v1+)
- 리스크 엔진(VaR/CVaR, 익스포저 제한)
- 레짐 분석(HMM/체제 필터)
- 포트폴리오 최적화(리스크 패리티 등)
- 프론트 분리 배포(Vercel), API 별도 호스팅

## 15. 프로젝트 구조
```
stock-dashboard/
├── collector/              # FDR 데이터 수집
│   ├── __init__.py
│   ├── fdr_client.py       # FDR 래퍼
│   ├── ingest.py           # 수집 오케스트레이션
│   └── validators.py       # OHLCV 정합성 검증
├── research_engine/        # 분석 모듈
│   ├── __init__.py
│   ├── factors.py          # 팩터 생성
│   ├── strategies.py       # 전략 엔진 (3종)
│   └── backtest.py         # 백테스트 실행기
├── api/                    # FastAPI 서버
│   ├── __init__.py
│   ├── main.py             # 앱 엔트리포인트
│   ├── routers/            # 엔드포인트별 라우터
│   ├── services/           # 비즈니스 로직
│   ├── repositories/       # DB 접근 계층
│   └── schemas/            # Pydantic 모델
├── dashboard/              # React + Recharts SPA
│   ├── package.json
│   ├── src/
│   └── public/
├── db/                     # DB 관련
│   ├── models.py           # SQLAlchemy 모델
│   └── alembic/            # 마이그레이션
├── scripts/                # 유틸리티 스크립트
├── tests/                  # 테스트
│   ├── unit/
│   └── integration/
├── docs/                   # 문서
├── dev/                    # dev-docs (active/done)
├── .env.example            # 환경변수 템플릿
├── pyproject.toml          # Python 프로젝트 설정
└── alembic.ini             # Alembic 설정
```

## 16. 의존성
### Python (pyproject.toml)
- **Core**: `financedatareader`, `sqlalchemy[asyncio]`, `psycopg2-binary`, `fastapi`, `uvicorn`, `pydantic`, `alembic`
- **Analysis**: `pandas`, `numpy`
- **Dev**: `pytest`, `ruff`, `httpx` (테스트 클라이언트)

### Dashboard (package.json)
- **Core**: `react`, `recharts`, `axios`, `react-router-dom`
- **Dev**: `vite`, `typescript`, `eslint`

## 17. 환경 변수 (.env.example)
```
DATABASE_URL=postgresql://user:pass@host:port/dbname
FDR_TIMEOUT=30
LOG_LEVEL=INFO
ALERT_WEBHOOK_URL=            # Discord webhook (배치 실패 알림)
PYTHONUTF8=1
```

## 18. 명시적 가정 (구 15절)
- 본 문서는 코드가 없는 초기 저장소를 기준으로 작성한다.
- 구현 시 모든 파일 인코딩은 UTF-8을 사용한다.
- v0에서 실거래 자동주문은 수행하지 않는다.
- Hantoo(한국투자증권) REST API 통합은 배포 직전 단계(v0.9+)로 이연한다. 1~4주차는 FDR 단일 소스로 개발한다.
