# Phase 4 Verification — 빅뱅 Cut-over
> Gen: silver
> Last Updated: 2026-05-10

## 정책 — "Show, don't claim"

> 체크박스는 evidence가 이 파일 또는 하위 step-N-<topic>.md에 paste되고 사용자가 본 후에만 표시 가능.
> 빅뱅 cut-over의 smoke test 결과는 반드시 curl 응답 dump + 스크린샷 형태로 paste.

---

## 진행 현황

| Step | 주제 | evidence 파일 | PNG | 상태 |
|---|---|---|---|---|
| P4-1 | git tag v-bronze-final | `step-1-tag.md` | — | ✅ 완료 |
| P4-2 | App.tsx 라우트 정리 | `step-2-routes.md` | `figures/step-2-redirect.png` | ✅ 완료 |
| P4-3 | Bronze 코드 삭제 | `step-3-code-delete.md` | `figures/step-3-silver-pages.png` | ✅ 완료 |
| P4-4 | DROP migration | `step-4-migration.md` | — | ✅ 완료 |
| P4-5 | Agentic tool 정리 | `step-5-agentic.md` | — | ✅ 완료 |
| P4-6 | 빅뱅 배포 + smoke test | `step-6-cutover.md` | `figures/step-6-prod-compare.png` | ✅ 완료 |
| P4-7 | 1주 monitoring | `step-7-monitoring.md` | `figures/p4-7-tab-a-loaded.png` `figures/p4-7-tab-b-strategy.png` `figures/p4-7-tab-c-portfolio.png` `figures/p4-7-mobile-768.png` | ✅ 완료 |

---

## PNG 의무 항목

| 파일명 | 내용 | 해당 게이트 |
|---|---|---|
| `figures/step-2-redirect.png` | Bronze 경로 → `/silver/compare` redirect 브라우저 확인 | G2.2 |
| `figures/step-3-silver-pages.png` | Bronze 삭제 후 Silver 페이지 정상 렌더링 | G3.2 |
| `figures/step-6-prod-compare.png` | prod `/silver/compare` Tab A KPI 렌더링 | G6.1 |

---

## Evidence 파일 형식

```markdown
## G<step>.<n> — <검증 항목>

**명령**: <실행한 1줄>
**Raw output / 스크린샷**: <코드 블록 또는 PNG 임베드>
**검증 결과**: ✅ PASS / ❌ FAIL — <근거>
```
