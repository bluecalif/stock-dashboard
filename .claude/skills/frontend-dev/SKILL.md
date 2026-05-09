---
name: frontend-dev
description: Stock Dashboard 프론트엔드 개발 가이드. React, Recharts, Vite, TypeScript. 가격/수익률/상관/전략 성과 시각화. API 소비, 컴포넌트 구조, 차트 패턴. Silver gen 작업 시(/silver/compare, CompareMainPage, KpiCard, EquityChart, AssetPickerDrawer, 다크 톤, 모바일 768px) `references/silver-design.md`의 디자인 토큰·카드 레시피·차트 그라디언트·pill 셀렉터·반응형 규칙을 함께 로드.
---

# Frontend Development Guidelines

## Purpose

Stock Dashboard 프론트엔드 개발 가이드.
React + Recharts + Vite + TypeScript 기반 SPA. FastAPI 백엔드 API를 소비하여 7개 자산의 가격/분석/전략 데이터를 시각화.

## When to Use This Skill

- dashboard 컴포넌트 구현
- 차트/시각화 (Recharts) 작업
- API 클라이언트 코드 작성
- 페이지/라우팅 추가
- TypeScript 타입 정의

---

## Architecture Overview

```
dashboard/
├── public/
├── src/
│   ├── main.tsx              # 앱 엔트리포인트
│   ├── App.tsx               # 라우팅 루트
│   ├── api/                  # API 클라이언트
│   │   ├── client.ts         # axios 인스턴스
│   │   ├── prices.ts         # /v1/prices 호출
│   │   ├── factors.ts        # /v1/factors 호출
│   │   ├── signals.ts        # /v1/signals 호출
│   │   └── backtests.ts      # /v1/backtests 호출
│   ├── components/           # 재사용 컴포넌트
│   │   ├── charts/           # Recharts 차트 컴포넌트
│   │   ├── layout/           # Header, Sidebar, Layout
│   │   └── common/           # 공용 UI (Loading, Error, Select)
│   ├── pages/                # 페이지 컴포넌트
│   │   ├── PricePage.tsx
│   │   ├── FactorPage.tsx
│   │   ├── StrategyPage.tsx
│   │   └── BacktestPage.tsx
│   ├── hooks/                # 커스텀 훅
│   ├── types/                # TypeScript 타입 정의
│   │   └── api.ts            # API 응답 타입
│   └── utils/                # 유틸리티
├── package.json
├── tsconfig.json
├── vite.config.ts
└── index.html
```

---

## Core Rules (5 Rules)

### 1. API 타입 동기화

```typescript
// types/api.ts — 백엔드 Pydantic 스키마와 1:1 매칭
interface PriceDaily {
  asset_id: string;
  date: string;        // ISO date
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  source: string;
}

interface FactorDaily {
  asset_id: string;
  date: string;
  factor_name: string;
  value: number;
}
```

### 2. API 클라이언트 중앙화

```typescript
// api/client.ts
import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

export default apiClient;
```

```typescript
// api/prices.ts
import apiClient from "./client";
import type { PriceDaily } from "../types/api";

export async function fetchPrices(
  assetId: string, from: string, to: string
): Promise<PriceDaily[]> {
  const { data } = await apiClient.get("/v1/prices/daily", {
    params: { asset_id: assetId, from, to },
  });
  return data;
}
```

### 3. Recharts 차트 패턴

```tsx
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

function PriceChart({ data }: { data: PriceDaily[] }) {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data}>
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="close" stroke="#2563eb" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

**규칙**:
- 항상 `ResponsiveContainer`로 감싸기
- `dot={false}` 일봉 데이터에서 (데이터 포인트 많음)
- 숫자 포맷: `toLocaleString()` 사용

### 4. 컴포넌트 구조

```
Page (데이터 fetch + 상태 관리)
  └── Chart/Table (props로 데이터 수신, 순수 렌더링)
```

- **Page**: API 호출, 로딩/에러 상태, 필터 관리
- **Chart/Table**: props만 받아서 렌더링. API 호출 금지
- 커스텀 훅으로 데이터 fetch 로직 분리 가능

### 5. 환경 변수

```
# .env (dashboard 로컬)
VITE_API_BASE_URL=http://localhost:8000
```

- `VITE_` 접두사 필수 (Vite 규칙)
- 하드코딩된 API URL 금지

---

## Dashboard 핵심 화면 (4개)

| 페이지 | 데이터 소스 | 주요 차트 |
|--------|------------|-----------|
| 가격 | `/v1/prices/daily` | 라인차트 (OHLCV), 멀티 자산 비교 |
| 팩터 | `/v1/factors` | SMA/EMA 오버레이, RSI, 변동성 |
| 전략 신호 | `/v1/signals` | 매수/매도 마커 오버레이 |
| 백테스트 | `/v1/backtests/{id}/equity` | 에쿼티 커브, 드로다운, 트레이드 로그 테이블 |

---

## Anti-Patterns

| Pattern | Problem |
|---------|---------|
| Chart 컴포넌트에서 API 직접 호출 | 재사용 불가, 테스트 어려움 |
| API URL 하드코딩 | 환경별 배포 불가 |
| `any` 타입 사용 | 타입 안전성 상실 |
| ResponsiveContainer 없이 고정 크기 | 반응형 깨짐 |
| useEffect 내 미정리 fetch | 메모리 누수, 경쟁 상태 |

---

## Zustand Store 패턴 (Post-MVP)

```typescript
// src/store/authStore.ts
import { create } from "zustand";

interface AuthState {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  login: async (email, password) => {
    const res = await authApi.login(email, password);
    set({ user: res.user, token: res.access_token });
  },
  logout: () => set({ user: null, token: null }),
}));
```

**규칙**: Zustand은 공유 상태(auth, chat, chart 설정)에만 사용. 페이지 로컬 상태는 기존 useState 유지.

## SSE 스트리밍 훅 (Post-MVP)

```typescript
// src/hooks/useSSE.ts — fetch + ReadableStream (POST 지원)
async function streamChat(sessionId: string, content: string, onEvent: (e: SSEEvent) => void) {
  const res = await fetch(`${API_BASE}/v1/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  // SSE 라인 파싱 루프...
}
```

**규칙**: EventSource는 GET 전용 → POST SSE는 반드시 fetch + ReadableStream 사용.

## Auth 라우트 가드 (Post-MVP)

```tsx
// src/components/auth/ProtectedRoute.tsx
function ProtectedRoute({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user);
  if (!user) return <Navigate to="/login" />;
  return <>{children}</>;
}
```

**규칙**: 기존 6개 페이지는 공개 유지. chat/memory 관련 라우트만 ProtectedRoute 적용.

---

## Silver Visual System (rev1)

silver-rev1은 다크 네이비 톤 + 카드형 KPI + 면적 차트 + pill 셀렉터 + 모바일 필수의 별도 시각 시스템을 가진다. `pages/silver/*` 디렉터리 작업 시(예: `CompareMainPage`, `KpiCard`, `EquityChart`, `AssetPickerDrawer`, `IndicatorCard`, `SignalDetailPage`, 모바일 768px 반응형) 다음 파일을 함께 읽어 디자인 토큰과 컴포넌트 레시피를 따른다:

→ **`.claude/skills/frontend-dev/references/silver-design.md`**

포함 내용:
- 다크 톤 디자인 토큰 (palette / radius / shadow) — 헥스 하드코딩 금지
- KpiCard 4종 레시피 (큰 숫자 + 미니 스파크라인 + 푸터 + 양/음 색)
- EquityChart Recharts 레시피 (녹색 면적 그라디언트 + 멀티 시리즈 색 순서 + 피크 callout)
- Pill 셀렉터 (기간 / 적립금 입력)
- Top nav (D-12 상단 가로) + AssetPickerDrawer (Tab별 universe 분기)
- 모바일 768px 규칙 (KPI 1열, 차트 세로 스택, drawer 풀스크린)
- silver-rev1 anti-patterns 9건

레퍼런스 시각: `docs/UX-design-ref.JPG` (다크 SaaS 대시보드 톤). silver IA에 맞춰 톤·카드 패턴만 차용 (사이드바 → 상단 가로 nav).

Bronze 페이지(`PricePage`, `CorrelationPage`, `DashboardPage`, `StrategyPage`) 작업 시에는 이 reference 무시 — 기존 톤 유지.

---

## Related Docs

- `docs/masterplan-v0.md` - API 명세 (섹션 8), 대시보드 화면 정의
- `docs/silver-masterplan.md` §4 - silver IA & 화면 명세 (Compare 3탭, AssetPickerDrawer 와이어프레임)
- `docs/UX-design-ref.JPG` - silver 다크 톤 시각 레퍼런스
- `docs/post-mvp-implementation-sketch.md` - Post-MVP 구현 스케치
- `.claude/skills/backend-dev/SKILL.md` - 백엔드 API 패턴 (프론트가 소비)
- `.claude/skills/silver-simulation/SKILL.md` - silver 시뮬레이션 도메인 (KPI 시그니처 정합)
- `.claude/skills/langgraph-dev/SKILL.md` - LangGraph SSE 백엔드 패턴

---

**Skill Status**: Core guide + Post-MVP Zustand/SSE/Auth + Silver Visual System (references/silver-design.md).
