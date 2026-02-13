# Phase 5: Frontend
> Last Updated: 2026-02-13
> Status: In Progress (Stage C 진행중, 7/10)

## 1. Summary (개요)

**목적**: FastAPI 백엔드 API(12개 엔드포인트)를 소비하여 7개 자산의 가격/분석/전략 데이터를 시각화하는 React SPA 대시보드 구축.

**범위**: Vite + React 18 + TypeScript 프로젝트 초기화부터 6개 페이지 완성까지.

**예상 결과물**:
- React SPA 대시보드 (6개 페이지)
- Axios 기반 API 클라이언트 + TypeScript 타입 정의
- Recharts 차트 컴포넌트 (라인차트, 히트맵, 에쿼티 커브, 매매 마커 등)
- 사이드바 네비게이션 + 반응형 레이아웃

## 2. Current State (현재 상태)

- **백엔드 API 완료**: 12개 엔드포인트 운영 중 (405 tests)
- **DB**: price_daily 5,573+, factor_daily 55K+, signal_daily 15K+, backtest 21 runs
- **프론트엔드**: Stage C 진행중 — 가격 차트, 수익률 비교, 상관 히트맵, 팩터 현황(FactorChart) 완료
- **환경**: Node.js v20.16.0, npm 10.8.1, Vite 6.4, React 19, TS 5.9

## 3. Target State (목표 상태)

| 영역 | 목표 |
|------|------|
| 프로젝트 구조 | Vite + React 18 + TypeScript + TailwindCSS |
| API 클라이언트 | Axios 인스턴스 + 14개 타입 정의 (백엔드 스키마 1:1) |
| 페이지 | 6개 (홈/가격/상관/팩터/시그널/전략성과) |
| 차트 | Recharts 기반 (라인, 히트맵, 에쿼티커브, 마커 오버레이) |
| 레이아웃 | 사이드바 네비게이션 + 반응형 메인 콘텐츠 |
| 라우팅 | React Router v6 (6개 경로) |

## 4. Implementation Stages

### Stage A: 기반 구조 (Step 5.1~5.3)
Vite 프로젝트 생성, 의존성 설치, API 클라이언트 + 타입, 레이아웃 셸.

### Stage B: 핵심 차트 (Step 5.4~5.5)
가격 차트 페이지 (라인/캔들, 자산 선택) + 정규화 누적수익률 비교 차트.

### Stage C: 분석 시각화 (Step 5.6~5.8)
상관 히트맵, 팩터 현황 (RSI/MACD), 시그널 타임라인 (매매 마커 오버레이).

### Stage D: 전략 성과 + 홈 (Step 5.9~5.10)
에쿼티 커브 비교 + 메트릭스 카드 + 거래 이력 테이블, 대시보드 홈 (요약 카드 + 미니 차트).

## 5. Task Breakdown

| Step | Task | Size | Stage | 의존성 |
|------|------|------|-------|--------|
| 5.1 | Vite + React 18 + TS 프로젝트 초기화 | M | A | 없음 |
| 5.2 | API 클라이언트 (Axios) + 타입 정의 | M | A | 5.1 |
| 5.3 | 레이아웃 (사이드바 + 메인 + React Router) | M | A | 5.1 |
| 5.4 | 가격 차트 페이지 (라인차트, 자산/기간 선택) | L | B | 5.2, 5.3 |
| 5.5 | 수익률 비교 차트 (정규화 누적수익률) | M | B | 5.4 |
| 5.6 | 상관 히트맵 (correlation matrix) | M | C | 5.2, 5.3 |
| 5.7 | 팩터 현황 (RSI/MACD 서브차트 + 비교 테이블) | M | C | 5.2, 5.3 |
| 5.8 | 시그널 타임라인 (가격 + 매매 마커 오버레이) | M | C | 5.4 |
| 5.9 | 전략 성과 비교 (에쿼티 커브 + 메트릭스 + 거래 이력) | L | D | 5.2, 5.3 |
| 5.10 | 대시보드 홈 (요약 카드 + 미니 차트) | M | D | 5.2, 5.3 |

**Size 분포**: S: 0, M: 8, L: 2, XL: 0 — **총 10 tasks**

## 6. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| API CORS 이슈 | 프론트-백 통신 불가 | 저 | 이미 localhost:5173 허용 설정 완료 |
| 대량 데이터 렌더 성능 | UX 저하 | 중 | Pagination 활용, 날짜 범위 제한, dot={false} |
| Recharts 히트맵 미지원 | 상관행렬 시각화 불가 | 중 | 커스텀 셀 렌더 또는 SVG 직접 구현 |
| TypeScript 타입 불일치 | 런타임 에러 | 저 | 백엔드 Pydantic 스키마와 1:1 매칭 검증 |

## 7. Dependencies (의존성)

### 내부
- `backend/api/` — 12개 엔드포인트 (Phase 4 완료)
- `backend/api/schemas/` — 14개 Pydantic 클래스 (TypeScript 타입 기준)

### 외부 (npm)
- `react` (18.x), `react-dom`, `react-router-dom` (6.x)
- `recharts` (2.x) — 차트 라이브러리
- `axios` — HTTP 클라이언트
- `tailwindcss` (3.x) — 유틸리티 CSS
- `vite` (5.x), `typescript` (5.x) — 빌드/타입
