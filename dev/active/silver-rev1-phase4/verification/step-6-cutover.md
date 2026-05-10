# P4-6 빅뱅 배포 Smoke Test Verification

> Date: 2026-05-10
> CI: `2d66c8c` → success → Railway + Vercel 자동 배포

---

## G6.1 — prod `/silver/compare` 렌더링

**명령**: Puppeteer → `https://stock-dashboard-alpha-lilac.vercel.app/silver/compare`

**Raw output**:
```
Final URL: https://stock-dashboard-alpha-lilac.vercel.app/silver/compare
KPI/table found: ✅
```

**스크린샷**: `figures/step-6-prod-compare.png`
- Tab A: QQQ 4.6억원 (+284.0%) / SPY 3.4억원 (+179.5%) / KS200 4.6억원 (+281.4%)
- 10년 3개 시리즈 차트 정상 렌더링
- "한 줄 해석" 카드 표시

**검증 결과**: ✅ PASS

---

## G6.2 — KPI 정합성 (Phase 2 fixture 기준)

**명령**:
```bash
curl -X POST https://backend-production-e5bc.up.railway.app/v1/silver/simulate/replay \
  -d '{"asset_code":"QQQ","monthly_amount":1000000,"period_years":10}'
```

**Raw output**:
```
asset_code: QQQ
final_asset_krw: 464625184
total_return: 2.8399
annualized_return: 0.144
yearly_worst_mdd: -0.2624
```

**검증 결과**: ✅ PASS — Phase 2 fixture (2.84 / 0.144 / -0.2624) 일치

---

## G6.3 — Bronze 경로 redirect (prod)

**명령**: Puppeteer — prod Bronze 경로 접근 후 최종 URL

**Raw output**:
```
/prices   → /silver/compare ✅
/strategy → /silver/compare ✅
/dashboard → /silver/compare ✅
```

**검증 결과**: ✅ PASS

---

## G6.4 — backtest 라우터 없음

**명령**: `curl https://backend-production-e5bc.up.railway.app/openapi.json | python -c "..."`

**Raw output**:
```
backtest routes (should be 0): ['/v1/analysis/strategy-backtest']
silver routes: ['/v1/silver/simulate/replay', '/v1/silver/simulate/strategy',
                '/v1/silver/simulate/portfolio', '/v1/fx/usd-krw']
total routes: 30
```

> `/v1/analysis/strategy-backtest`는 `analysis.py` 유지분 (마스터플랜 §5.3 유지 목록).
> `backtests.py` 라우터 (`/v1/backtests/*`) 완전 제거 ✅

**검증 결과**: ✅ PASS

---

## CI/CD 이력

| 커밋 | 내용 | CI |
|------|------|----|
| `3152c2e` | P4-1~P4-5 빅뱅 준비 | ❌ lint 실패 |
| `22f3d36` | ruff auto-fix | ❌ 테스트 실패 |
| `bac648e` | backtest 테스트 제거 | ❌ 추가 테스트 실패 |
| `1cb2dd2` | ruff 추가 수정 | ❌ |
| `2d66c8c` | Silver gen 기준 테스트 수정 | ✅ PASS → Railway+Vercel 배포 |

---

## 결론: P4-6 전 게이트 PASS ✅
