# Silver rev1 — Phase 1: Debug History
> Gen: silver
> Last Updated: 2026-05-09
> Phase: silver-rev1-phase1 (Data Infra)

> Phase 1 진행 중 발생한 버그/원인/수정/교훈을 시간순으로 기록. 동일 이슈 재발 시 우선 검색.

## 형식

```
### YYYY-MM-DD — <한줄 요약>
**증상**: 어떤 명령/조작이 어떤 에러로 실패
**원인**: 분석 결과 (외부/내부 / 한 번에 하나만 가설 검증)
**수정**: 코드/설정/명령 변경
**교훈**: 재발 방지 / 다음 Phase에 인계할 사항
**관련 commit**: <hash>
```

---

## 항목

### 2026-05-09 — NVDA volume int32 overflow → validation_failed

**증상**: `ingest_asset('NVDA', '2016-05-08', '2026-05-09')` → `validation_failed: negative_volume:5rows`. 다른 7자산은 정상.

**원인**: `fdr_client.py:62` `df["volume"].fillna(0).astype(int)`. Windows 환경에서 pandas가 `int`를 int32로 해석. NVDA 2016~2017년 거래량 최대 3,692,928,000이 int32 max(2,147,483,647) 초과 → overflow로 음수 반환 (예: 2,175,344,000 → -2,119,623,296).

**수정**: `astype(int)` → `astype("int64")` (fdr_client.py 1줄 변경)

**교훈**: 미국 대형주(특히 NVDA, AAPL, MSFT 등 고거래량 종목)의 volume은 int32 범위를 초과할 수 있다. volume 컬럼은 반드시 int64 사용. 향후 Silver 신규 자산 추가 시 동일 이슈 발생 가능 — fdr_client.py 수정으로 전체 해소.

**관련 commit**: (P1-4 commit)
