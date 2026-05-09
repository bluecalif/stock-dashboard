# Phase 1 — Verification Evidence

> 정책: project-overall-context.md §0 / silver-rev1-phase1-context.md §0 — "Show, don't claim"
> 모든 step 종료 시 본 디렉터리에 evidence markdown 작성 의무.

## 파일 구조

```
verification/
├── README.md                          (본 파일)
├── step-1-schema.md                   ✅ P1-1 (commit 7d457a2)
├── step-2-symbol-map.md               (P1-2 종료 시)
├── step-3-fx.md                       (P1-3 종료 시)
├── step-4-backfill.md                 (P1-4 종료 시)
├── step-5-padding.md                  (P1-5 종료 시)
├── step-6-wbi.md                      (P1-6 종료 시)
└── figures/
    ├── step-4-backfill-rowcount.png  (P1-4 자산별 row count bar)
    ├── step-5-padding-jepi.png       (P1-5 padding 시계열)
    └── step-6-wbi-visual.png         (P1-6 WBI 가격 + 수익률 분포)
```

## 게이트 형식 (전 step 공통)

각 markdown 파일은 게이트별로 다음 3단 구조:

```markdown
## G<step>.<n> — <검증 항목>

**명령**: <실행한 1줄>
**Raw output**: <표 / 코드 블록 / PNG 임베드>
**검증 결과**: ✅ PASS / ❌ FAIL — <근거>
```

PNG 임베드: `![title](figures/<name>.png)`

## 진행 현황

| Step | Evidence 파일 | Status |
|---|---|---|
| P1-1 | step-1-schema.md | ✅ |
| P1-2 | step-2-symbol-map.md | ✅ |
| P1-3 | step-3-fx.md | TODO |
| P1-4 | step-4-backfill.md + PNG | TODO |
| P1-5 | step-5-padding.md + PNG | TODO |
| P1-6 | step-6-wbi.md + PNG | TODO |
