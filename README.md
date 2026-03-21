# Stock Dashboard

7개 자산(KOSPI200, 삼성전자, SK하이닉스, SOXL, BTC, Gold, Silver)의 일봉 데이터를 수집·분석·시각화하는 풀스택 대시보드.

15개 팩터 분석, 3개 전략 백테스트, AI 채팅 상담을 제공합니다.

## 주요 기능

- **가격 대시보드**: 7개 자산의 OHLCV 데이터 조회, 정규화 누적수익률 비교
- **팩터 분석**: 수익률·추세·모멘텀·변동성·거래량 등 15개 팩터
- **전략 & 백테스트**: 모멘텀/추세/평균회귀 3개 전략, 에쿼티 커브, 성과 메트릭
- **상관 분석**: 자산 간 rolling correlation 히트맵
- **지표/시그널**: 전략 신호 성공률, 가격 차트 위 매수/청산 마커
- **AI 채팅**: LangGraph + GPT 기반 Agentic 분석 상담 (사용자 맥락 인식)
- **인증**: JWT 기반 회원가입/로그인/탈퇴

## 스크린샷

| 정규화 가격 비교 | 상관행렬 히트맵 |
|:---:|:---:|
| ![price](docs/e2e_report/1_price_normalized.png) | ![correlation](docs/e2e_report/2_correlation_heatmap.png) |

| 에쿼티 커브 | 전략 성과 비교 |
|:---:|:---:|
| ![equity](docs/e2e_report/3_equity_curves.png) | ![strategy](docs/e2e_report/4_strategy_comparison.png) |

## 아키텍처

```
scheduler → collector (FDR) → PostgreSQL → research_engine → API (FastAPI) → dashboard (React)
```

```
stock-dashboard/
├── backend/
│   ├── api/              # FastAPI 라우터, 서비스, 리포지토리
│   ├── collector/         # FinanceDataReader 기반 일봉 수집
│   ├── research_engine/   # 팩터 생성, 전략 신호, 백테스트
│   ├── db/               # SQLAlchemy 모델, Alembic 마이그레이션
│   ├── config/           # 설정 & 로깅
│   └── tests/            # 860+ 테스트
├── frontend/
│   ├── src/pages/        # 9개 페이지
│   ├── src/components/   # 차트, 레이아웃, 인증 컴포넌트
│   └── src/store/        # Zustand 상태 관리
└── docs/                 # 설계 문서, E2E 리포트
```

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic 2.0 |
| Database | PostgreSQL (Railway) |
| Data | FinanceDataReader |
| AI | LangGraph, LangChain, OpenAI GPT |
| Frontend | React 19, TypeScript, Vite, Recharts, Zustand |
| Styling | Tailwind CSS |
| Migration | Alembic |
| Auth | JWT (python-jose, bcrypt) |

## 시작하기

### 사전 요구사항

- Python 3.11+
- Node.js 18+
- PostgreSQL (로컬 또는 Railway)

### 환경 변수

`.env` 파일을 `backend/` 디렉토리에 생성:

```env
DATABASE_URL=postgresql://user:pass@host:port/dbname
OPENAI_API_KEY=sk-...
JWT_SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:5173
PYTHONUTF8=1
```

### 백엔드 실행

```bash
cd backend
pip install -e ".[dev]"

# DB 마이그레이션
alembic upgrade head

# 데이터 수집 (최초 1회)
python -m scripts.collect

# 팩터/전략/백테스트 계산
python -m scripts.research

# 개발 서버
uvicorn api.main:app --reload
```

### 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

http://localhost:5173 에서 대시보드 확인.

## API 엔드포인트

| 경로 | 설명 |
|------|------|
| `GET /v1/health` | DB 헬스체크 |
| `GET /v1/assets` | 자산 목록 |
| `GET /v1/prices/daily` | 가격 조회 |
| `GET /v1/factors` | 팩터 조회 |
| `GET /v1/signals` | 전략 신호 조회 |
| `POST /v1/backtests` | 백테스트 실행 |
| `GET /v1/dashboard/summary` | 대시보드 요약 |
| `GET /v1/correlation` | 상관행렬 |
| `POST /v1/auth/signup` | 회원가입 |
| `POST /v1/auth/login` | 로그인 |
| `DELETE /v1/auth/me` | 회원 탈퇴 |
| `POST /v1/chat` | AI 채팅 (SSE) |
| `GET /v1/analysis/*` | 팩터/신호/백테스트 분석 |

## 테스트

```bash
cd backend
python -m pytest              # 전체 테스트 (860+)
python -m pytest -x           # 첫 실패 시 중단
ruff check .                  # 린트
```

## 데이터베이스 스키마

| 테이블 | 설명 |
|--------|------|
| `asset_master` | 7개 자산 정의 |
| `price_daily` | OHLCV 일봉 데이터 |
| `factor_daily` | 15개 팩터 값 |
| `signal_daily` | 전략별 매수/청산 신호 |
| `backtest_run` | 백테스트 실행 결과 |
| `backtest_equity_curve` | 에쿼티 커브 |
| `backtest_trade_log` | 거래 내역 |
| `users` | 사용자 계정 |
| `chat_sessions` / `chat_messages` | 채팅 이력 |
| `user_profiles` / `user_activity` | 사용자 프로필 & 활동 |

## 개발 이력

| Phase | 내용 |
|-------|------|
| MVP (0~7) | 수집, DB, 팩터, 전략, 백테스트, API, 프론트엔드 |
| Phase A | JWT 인증 |
| Phase B | AI 채팅 (LangGraph) |
| Phase C | 상관 분석 |
| Phase D | 지표 시각화 |
| Phase E | 전략 성과 분석 |
| Phase F | Agentic AI (분류기 + 도구 호출) |
| Phase G | 대화 맥락 인식 (요약, 프로필, 히스토리) |

## 라이선스

Private project.
