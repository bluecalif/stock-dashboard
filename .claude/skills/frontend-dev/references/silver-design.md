# Silver rev1 Visual System

> Loaded from `frontend-dev/SKILL.md` when working on `pages/silver/*` 또는 `/silver/compare` 화면. Bronze 페이지 작업 시에는 이 파일 무시.
>
> 시각 레퍼런스: `docs/UX-design-ref.JPG` (다크 네이비 SaaS 대시보드 톤). 톤·구조를 차용하되 silver IA(상단 가로 nav, 적립식 비교 3탭)에 맞춰 적용.

## 1. Why Silver gets its own visual system

Bronze 페이지 6종은 차트 중심의 데이터 분석 도구 톤이었지만, silver-rev1은 **초보 투자자용 적립식 비교 도구**(D-12)다. 정보 밀도보다 **숫자 한눈에 띄기 + 다크 톤 안정감 + 모바일 가독성**이 우선이라, 카드/차트/입력의 시각 패턴이 갈린다. 토큰을 명시해 두지 않으면 매번 추론으로 흔들리므로 이 파일에 고정.

`docs/UX-design-ref.JPG`의 핵심은 (a) 다크 네이비 셸 + 미세 글로우 카드, (b) 큰 숫자 + 미니 스파크라인 KPI, (c) 녹색 면적 차트 + 피크 툴팁 칩, (d) 작은 pill 셀렉터. 이 4가지가 silver Compare 페이지에 1:1 매핑된다.

---

## 2. Design tokens

추정 값 — 실제 시안과 비교 후 조정. CSS 변수 또는 Tailwind 토큰으로 명시:

```css
:root {
  /* Background */
  --bg-app: #0A0E1A;            /* 페이지 셸 (가장 어두운 네이비) */
  --bg-card: #131826;           /* 카드 기본 */
  --bg-card-elevated: #1A2030;  /* hover / 활성 카드 */
  --bg-pill-active: #2A3447;    /* pill 셀렉터 활성 상태 */
  --bg-pill-inactive: transparent;

  /* Border / glow */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-card: rgba(255, 255, 255, 0.08);
  --glow-card: 0 0 0 1px rgba(255, 255, 255, 0.04), 0 8px 32px rgba(0, 0, 0, 0.45);

  /* Text */
  --text-primary: #F1F5F9;      /* 큰 숫자, 본문 */
  --text-secondary: #94A3B8;    /* 카드 라벨, 메타 */
  --text-tertiary: #64748B;     /* 푸터, 비활성 */

  /* Accent */
  --accent-green: #3DD68C;            /* 면적 차트 라인 + 양수 KPI */
  --accent-green-soft: rgba(61, 214, 140, 0.18);   /* 차트 fill */
  --accent-green-glow: rgba(61, 214, 140, 0.35);   /* 피크 dot */
  --accent-blue: #60A5FA;             /* 멀티 시리즈 비교 자산 2 */
  --accent-blue-soft: rgba(96, 165, 250, 0.14);
  --accent-violet: #A78BFA;           /* 비교 자산 3 */
  --accent-amber: #F59E0B;            /* 위험/경고 카드 */
  --accent-red: #EF4444;              /* 음수 KPI (수익률 −) */

  /* Spacing */
  --radius-card: 16px;
  --radius-pill: 9999px;
  --space-card-padding: 20px;
  --space-section: 24px;
}
```

> Tailwind 환경이면 `tailwind.config.ts`의 `theme.extend.colors`에 매핑. 하드코딩 헥스 금지 — 토큰 통해 변경 가능하게 유지.

---

## 3. Typography

```
숫자 (KPI 큰 숫자):  font-size 32~40px / weight 600~700 / tabular-nums / letter-spacing -0.02em
숫자 (KPI 작은):     font-size 14~16px / weight 500
라벨 (카드 헤더):    font-size 12~13px / weight 500 / color text-secondary / uppercase letter-spacing 0.04em (선택)
본문:                font-size 14px / weight 400 / line-height 1.5
메타 (날짜/푸터):    font-size 11~12px / color text-tertiary
```

`tabular-nums` 또는 `font-variant-numeric: tabular-nums`로 KPI 카드 숫자 자릿수 정렬 — 비교 시 흔들림 방지.

---

## 4. KpiCard 레시피

레퍼런스: 상단 4개 "Today's sales / This week's / This month's / Last month's" 카드. silver Compare에서 4종 KPI(D-18)에 1:1 매핑:

| KPI 카드 | 라벨 | 큰 숫자 |
|---|---|---|
| 1 | "최종 자산" | `KRW 142,300,000` |
| 2 | "총 수익률" | `+18.6%` (양수 녹색 / 음수 빨강) |
| 3 | "연환산 수익률" | `+8.2%` |
| 4 | "연도 기준 최대 손실폭" | `−24%` (2022) |

```tsx
// components/silver/KpiCard.tsx
type Props = {
  label: string;                    // "최종 자산"
  value: string;                    // "KRW 142,300,000" (formatted)
  delta?: number;                   // 양/음 부호 결정 (선택)
  sparklineData?: { x: string; y: number }[];   // 미니 차트
  footer?: { date?: string; count?: number };   // "Oct 27 - Nov 02, 25  · 34"
  highlight?: { label: string; value: string };  // 피크 callout chip
};

function KpiCard({ label, value, delta, sparklineData, footer, highlight }: Props) {
  const tone = delta === undefined ? "neutral" : delta >= 0 ? "positive" : "negative";
  return (
    <div className="kpi-card">
      <div className="kpi-card__label">{label}</div>
      <div className={`kpi-card__value kpi-card__value--${tone}`}>{value}</div>
      {sparklineData && (
        <Sparkline data={sparklineData} tone={tone} highlight={highlight} />
      )}
      {footer && (
        <div className="kpi-card__footer">
          {footer.date && <CalendarIcon /> + footer.date}
          {footer.count !== undefined && <FolderIcon /> + footer.count}
        </div>
      )}
    </div>
  );
}
```

```css
.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-card);
  padding: var(--space-card-padding);
  box-shadow: var(--glow-card);
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 140px;
}
.kpi-card__label { color: var(--text-secondary); font-size: 12px; }
.kpi-card__value { color: var(--text-primary); font-size: 32px; font-weight: 700; font-variant-numeric: tabular-nums; }
.kpi-card__value--positive { color: var(--accent-green); }
.kpi-card__value--negative { color: var(--accent-red); }
.kpi-card__footer { color: var(--text-tertiary); font-size: 12px; display: flex; gap: 12px; align-items: center; margin-top: auto; }
```

피크 callout chip (레퍼런스의 "$14" 풍선): `position: absolute` + 작은 둥근 흰색 칩 + 작은 dot 점. 호버 시 표시. 모든 카드에 강제하지 말고 **눈에 띄는 단일 데이터 포인트가 있을 때만** (예: 최근 적립일).

---

## 5. EquityChart 레시피 (Recharts)

레퍼런스 메인 차트: 녹색 라인 + fill 그라디언트 + 피크 툴팁. silver의 누적 자산가치 KRW 곡선이 비교 자산 수만큼 멀티 시리즈로:

```tsx
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, defs, linearGradient, stop } from "recharts";

const SERIES_COLORS = ["#3DD68C", "#60A5FA", "#A78BFA", "#F59E0B", "#EF4444", "#94A3B8"];

function EquityChart({ data, assets }: { data: Row[]; assets: string[] }) {
  return (
    <ResponsiveContainer width="100%" height={360}>
      <AreaChart data={data} margin={{ top: 16, right: 16, bottom: 8, left: 8 }}>
        <defs>
          {assets.map((asset, i) => (
            <linearGradient key={asset} id={`grad-${asset}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={SERIES_COLORS[i]} stopOpacity={0.35} />
              <stop offset="100%" stopColor={SERIES_COLORS[i]} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
        <XAxis
          dataKey="date"
          stroke="#64748B"
          fontSize={11}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          stroke="#64748B"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `${(v / 10000).toFixed(0)}만`}
        />
        <Tooltip
          contentStyle={{
            background: "#1A2030",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 8,
            color: "#F1F5F9",
            fontSize: 12,
          }}
          cursor={{ stroke: "rgba(255,255,255,0.1)", strokeWidth: 1 }}
        />
        {assets.map((asset, i) => (
          <Area
            key={asset}
            type="monotone"
            dataKey={asset}
            stroke={SERIES_COLORS[i]}
            strokeWidth={2}
            fill={`url(#grad-${asset})`}
            dot={false}
            activeDot={{ r: 4, fill: SERIES_COLORS[i], stroke: "#0A0E1A", strokeWidth: 2 }}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );
}
```

규칙:
- 첫 번째 시리즈는 항상 녹색(레퍼런스 메인 톤). 두 번째부터 blue/violet/amber 순.
- `dot={false}` 일봉 데이터에서 (데이터 포인트 많음).
- `activeDot`은 호버 시만 표시, 외곽선에 `--bg-app` 색을 둘러 배경과 구분.
- 그리드는 가로선만, 매우 옅게 (`rgba(255,255,255,0.04)`).
- 축 레이블 `font-size: 11`, `color: --text-tertiary`. axisLine/tickLine 제거해 노이즈 줄임.
- Y축 KRW 단위 — `만`, `억` 한국어 단위로 변환 권장.

피크 callout chip: 별도 `<Customized>` 또는 마지막 데이터 포인트 위에 absolute div로 그려 강조 (예: 최근 적립 시점 가치).

padding 구간(JEPI 5년 padding 등 D-2): 영역 fill을 회색 톤(`rgba(148,163,184,0.15)`)으로 별도 시리즈로 그리거나, X축 영역에 `<ReferenceArea>`로 표시 + "padding 구간" 라벨.

---

## 6. Pill 셀렉터 (입력 패널)

레퍼런스 우측 상단 "7d / 30d" pill. silver의 기간/적립금 선택에 동일 패턴:

```tsx
// components/silver/PillGroup.tsx
function PillGroup<T extends string | number>({
  options, value, onChange, ariaLabel,
}: { options: { value: T; label: string }[]; value: T; onChange: (v: T) => void; ariaLabel: string }) {
  return (
    <div role="radiogroup" aria-label={ariaLabel} className="pill-group">
      {options.map((opt) => (
        <button
          key={opt.value}
          role="radio"
          aria-checked={value === opt.value}
          className={`pill ${value === opt.value ? "pill--active" : ""}`}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
```

```css
.pill-group { display: inline-flex; gap: 4px; padding: 4px; background: var(--bg-card); border-radius: var(--radius-pill); border: 1px solid var(--border-subtle); }
.pill { padding: 6px 14px; border-radius: var(--radius-pill); background: transparent; color: var(--text-secondary); font-size: 13px; border: none; cursor: pointer; }
.pill--active { background: var(--bg-pill-active); color: var(--text-primary); }
```

silver 입력 패널 사용처 (D-18 §1.1 lock):
- 기간: `[3년][5년][●10년]`
- 적립금: `[30][50][●100][200][300]만원`

---

## 7. Top nav (D-12 상단 가로)

레퍼런스는 좌측 사이드바지만, silver-rev1은 D-12에 따라 **상단 가로 nav** 채택. 모바일에서 가로 스크롤 또는 hamburger(미정).

```tsx
<header className="top-nav">
  <div className="top-nav__brand">Stock Dashboard</div>
  <nav className="top-nav__items">
    <NavLink to="/silver/compare">적립식 비교</NavLink>
    <NavLink to="/silver/signals">신호</NavLink>
    <NavLink to="/silver/chat">Chat</NavLink>
  </nav>
  <div className="top-nav__profile">
    <ProfileMenu />
  </div>
</header>
```

```css
.top-nav { display: flex; align-items: center; justify-content: space-between; padding: 12px 24px; background: var(--bg-app); border-bottom: 1px solid var(--border-subtle); }
.top-nav__items { display: flex; gap: 4px; }
.top-nav__items a { padding: 8px 14px; border-radius: 8px; color: var(--text-secondary); font-size: 14px; text-decoration: none; }
.top-nav__items a.active { background: var(--bg-card); color: var(--text-primary); }
```

---

## 8. AssetPickerDrawer (D-12 + D-19/20/21)

`+` 버튼 클릭 시 우측에서 슬라이드 인. Tab별 universe 다르므로 props로 분기:

```tsx
type Props = {
  open: boolean;
  onClose: () => void;
  universe: string[];                         // D-19/20/21 별 후보
  selected: string[];
  onChange: (selected: string[]) => void;
  maxSelect?: number;                         // Tab A는 6종, Tab B는 3종
};
```

```css
.drawer { position: fixed; right: 0; top: 0; bottom: 0; width: 360px; background: var(--bg-card); border-left: 1px solid var(--border-card); transform: translateX(100%); transition: transform 200ms ease; }
.drawer--open { transform: translateX(0); }
@media (max-width: 768px) { .drawer { width: 100vw; } }   /* 모바일 풀스크린 */
```

체크박스 리스트 + 카테고리 그룹(US ETF / KR / Crypto / Synthetic) + [추가] [취소] 푸터 버튼.

---

## 9. 모바일 (768px breakpoint, D-12)

```css
@media (max-width: 768px) {
  /* nav: 가로 스크롤 (hamburger 미정 — 시안 후 결정) */
  .top-nav__items { overflow-x: auto; flex-wrap: nowrap; }

  /* KPI 카드: 1열 세로 스택 */
  .kpi-grid { grid-template-columns: 1fr; }

  /* 차트: 세로 스택 */
  .chart-row { flex-direction: column; }

  /* drawer: 풀스크린 모달 */
  .drawer { width: 100vw; }

  /* 카드 padding 축소 */
  .kpi-card { min-height: 110px; padding: 16px; }
  .kpi-card__value { font-size: 26px; }
}
```

데스크톱 우선 디자인 후 모바일 검증, **쇼크 테스트**: iPhone SE(375px) 폭에서 KPI 4종 + 차트 + 입력 패널이 정상 렌더링되는지 확인.

---

## 10. Anti-Patterns

| 함정 | 증상 | 올바른 방식 |
|---|---|---|
| 헥스 색 하드코딩 | 토큰 변경 시 누락 발생 | CSS 변수 또는 Tailwind 토큰 사용 |
| 차트 라인 색을 임의로 | 비교 자산 색 충돌, 레퍼런스 톤과 어긋남 | `SERIES_COLORS` 상수 정의해 순서대로 |
| 라이트 모드 추가 | rev1 범위 외, 디자인 어긋남 | rev1은 다크 모드 단일. 라이트 토글은 후속 과제 |
| KPI 숫자에 일반 폰트 | 자릿수 흔들림 | `font-variant-numeric: tabular-nums` |
| 사이드바 레퍼런스 그대로 채택 | D-12 위반 (상단 가로 nav) | 사이드바는 톤·카드 패턴만 차용, IA는 상단 nav |
| ResponsiveContainer 없이 차트 고정 크기 | 모바일 깨짐 | 항상 `<ResponsiveContainer>`로 감싸기 |
| dot 표시 (일봉) | 데이터 포인트 너무 많음 | `dot={false}`, `activeDot`으로만 호버 표시 |
| 양/음 부호 무관하게 단색 | 수익률 직관 떨어짐 | 양수 `--accent-green`, 음수 `--accent-red` |
| padding 구간을 본 시리즈와 동일 톤 | D-2 사용자 혼동 | 회색 톤 + 라벨로 명시 구분 |

---

## Related

- `docs/silver-masterplan.md` §4 (IA & 화면 명세) — ASCII 와이어프레임
- `docs/UX-design-ref.JPG` — 다크 톤 시각 레퍼런스
- `dev/active/project-overall/project-overall-context.md` §3 D-12/D-18~D-21 — UI/universe lock
- `.claude/skills/silver-simulation/SKILL.md` — 백엔드 KPI 시그니처와 정합
