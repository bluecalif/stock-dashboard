# Phase 3 Verification — 프론트엔드 신규 페이지
> Gen: silver
> Last Updated: 2026-05-10

## 정책 — "Show, don't claim"

> 체크박스는 evidence가 이 파일 또는 하위 step-N-<topic>.md에 paste되고 사용자가 본 후에만 표시 가능.
> UI / E2E step은 **반드시 PNG 스크린샷** 첨부. Claude의 "정상" 주장만으로는 체크 금지.

---

## 진행 현황

| Step | 주제 | evidence 파일 | PNG | 상태 |
|---|---|---|---|---|
| P3-1 | 라우트 등록 + SilverLayout | `step-1-routes.md` | `figures/step-1-*.png` | ✅ 완료 |
| P3-2 | 컴포넌트 + API 연동 | `step-2-components.md` | `figures/step-2-*.png` | ✅ 완료 |
| P3-3 | SignalDetailPage | `step-3-signals.md` | `figures/step-3-*.png` | ✅ 완료 |
| P3-4 | 모바일 768px | `step-4-mobile.md` | `figures/step-4-*.png` | ✅ 완료 |
| P3-5 | AssetPickerDrawer 분기 | `step-5-drawer.md` | `figures/step-5-*.png` | ⬜ 미착수 |

---

## Evidence 파일 형식

```markdown
## G<step>.<n> — <검증 항목>
**명령**: <실행한 명령 또는 조작>
**Raw output / 스크린샷**:
  - 파일: `figures/step-N-<topic>.png` (UI step)
  - 또는 코드 블록에 JSON / 수치 paste
**검증 결과**: ✅ PASS / ❌ FAIL — <근거>
```

---

## PNG 의무 항목

| 파일명 | 내용 | 해당 게이트 |
|---|---|---|
| `figures/step-1-route-desktop.png` | /silver/compare 데스크탑 첫 렌더링 | G1.1 |
| `figures/step-1-redirect.png` | /prices → /silver/compare redirect | G1.2 |
| `figures/step-2-tab-a-desktop.png` | Tab A 3자산 KPI + 차트 | G2.1 |
| `figures/step-2-tab-b.png` | Tab B 전략 A 결과 | G2.3 |
| `figures/step-2-tab-c.png` | Tab C 포트폴리오 결과 | G2.4 |
| `figures/step-2-jepi-padding.png` | JEPI padding 회색 영역 | G2.5 |
| `figures/step-3-signals-desktop.png` | SignalDetailPage RSI 탭 | G3.1 |
| `figures/step-4-mobile-nav.png` | 768px nav 가로 스크롤 | G4.1 |
| `figures/step-4-mobile-kpi.png` | 768px KPI 1열 | G4.2 |
| `figures/step-4-mobile-drawer.png` | 768px drawer 풀스크린 | G4.3 |
| `figures/step-4-iphonese.png` | 375px smoke test | G4.4 |
| `figures/step-5-drawer-tab-a.png` | Drawer Tab A 6종 | G5.1 |
| `figures/step-5-drawer-tab-b.png` | Drawer Tab B 3종 | G5.2 |
