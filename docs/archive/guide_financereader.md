네! 요청하신 **7종목 (KOSPI200, 삼성전자, SK하이닉스, SOXL ETF, 비트코인, 금, 은)**에 대해 **Python-기반 FinanceDataReader(이하 FDR)로 일별 시세 수집이 가능한지** 정리하면 아래와 같습니다. ([GitHub][1])

---

## 🎯 FinanceDataReader로 모두 수집 가능 여부

| 자산                | FDR 심볼                 | 수집 가능 여부 | 비고                      |
| ----------------- | ---------------------- | -------- | ----------------------- |
| **KOSPI 200 지수**  | `KS200`                | ✅        | 코스피200 지수 일별 OHLCV      |
| **삼성전자 주식**       | `005930`               | ✅        | 한국주식 시세                 |
| **SK하이닉스 주식**     | `000660`               | ✅        | 한국주식 시세                 |
| **SOXL ETF**      | `SOXL`                 | ✅        | 미국 상장 ETF (반도체 3배 레버리지) |
| **비트코인**          | `BTC/KRW` 또는 `BTC/USD` | ✅        | 암호화폐 시세                 |
| **금 선물 (Gold)**   | `GC=F`                 | ✅        | COMEX 금 선물              |
| **은 선물 (Silver)** | `SI=F`                 | ✅        | COMEX 은 선물              |

> 위 심볼들은 FDR이 기본으로 지원하는 주요 지수/주식/선물/암호화폐 심볼이며, **DataFrame 형태로 일별 OHLCV 데이터를 수집**할 수 있습니다. ([GitHub][1])

---

## 🧠 개별 정의 & 예시 코드

### 1) **KOSPI 200 지수**

```python
import FinanceDataReader as fdr
df_ks200 = fdr.DataReader('KS200', '2010-01-01')
```

*KS200*은 코스피200 지수(한국 증시 대표 지수)입니다. ([GitHub][1])

---

### 2) **삼성전자**

```python
df_samsung = fdr.DataReader('005930', '2010-01-01')
```

한국거래소(KRX) 상장주식으로 국내주식 1위 종목입니다. ([GitHub][1])

---

### 3) **SK하이닉스**

```python
df_hynix = fdr.DataReader('000660', '2010-01-01')
```

메모리 반도체 대표 종목입니다. ([GitHub][1])

---

### 4) **SOXL ETF**

```python
df_soxl = fdr.DataReader('SOXL', '2015-01-01')
```

SOXL은 미국에 상장된 **3배 레버리지 반도체 ETF**입니다. 미국 증시 데이터를 FDR에서 직접 불러옵니다. ([GitHub][1])

---

### 5) **비트코인**

일별 시세는 두 가지로 불러올 수 있습니다:

```python
df_btc_krw = fdr.DataReader('BTC/KRW', '2016-01-01')
df_btc_usd = fdr.DataReader('BTC/USD', '2016-01-01')
```

*BTC/KRW*는 원화 기준, *BTC/USD*는 달러 기준 비트코인 데이터입니다 (원화 거래소 기반 데이터). ([GitHub][1])

---

### 6) **금 선물 (Gold)**

```python
df_gold = fdr.DataReader('GC=F', '2010-01-01')
```

FDR은 대표 COMEX 금 선물 심볼인 *GC=F*도 지원합니다. ([GitHub][1])

---

### 7) **은 선물 (Silver)**

```python
df_silver = fdr.DataReader('SI=F', '2010-01-01')
```

대표 COMEX 은 선물 심볼인 *SI=F*로 수집 가능합니다. ([GitHub][1])

---

## 📌 공통 리턴 형식

FDR로 불러오는 모든 시계열은 아래와 같은 기본 컬럼을 갖습니다:

* `Open` (시가)
* `High` (고가)
* `Low` (저가)
* `Close` (종가)
* `Volume` (거래량)
* 인덱스는 날짜(YYYY-MM-DD) 형태

```python
df.head()
# returns:
# Date       Open    High     Low    Close   Volume
# 2010-01-04  xxx   xxx      xxx    xxx      xxx
```

---

## 🛠 활용시 주의사항

### ✔️ 1) 데이터 정확성

FDR은 여러 공공/웹 데이터 소스를 통합하여 크롤링/파싱하는 구조입니다.
→ 과거 데이터 품질은 비교적 안정적이나, 데이터 소스 변경이 있으면 일부 심볼에 영향이 있을 수 있습니다.

### ✔️ 2) 금/은 선물은 실제 **월물 계약 가격**과 다를 수 있음

FDR은 대표적인 선물 심볼(연속/롤링된 시계열)을 제공합니다. 실제 현물 가격과 차이가 있을 수 있으므로,
정확히 특정 월물별로 분리해야 하는 경우 **전용 선물 API(Bloomberg, Quandl)** 사용을 고려할 수 있습니다.

### ✔️ 3) SOXL ETF

SOXL은 거래량/가격 모두 잘 수집되나, **해외 거래소 시차**와 **휴장일**을 고려해야 합니다.

---

## 📌 전체 수집 템플릿 예

아래는 7종목을 한 번에 불러와 딕셔너리로 관리하는 기본 템플릿입니다:

```python
import FinanceDataReader as fdr

symbols = {
    "KOSPI200": "KS200",
    "Samsung": "005930",
    "Hynix": "000660",
    "SOXL": "SOXL",
    "BTC_KRW": "BTC/KRW",
    "Gold": "GC=F",
    "Silver": "SI=F"
}

data = {}
for name, sym in symbols.items():
    data[name] = fdr.DataReader(sym, '2010-01-01')

# 예: 삼성전자 시세
print(data["Samsung"].head())
```

---

## 📌 결론

✅ FinanceDataReader를 사용하면
→ **KOSPI200, 국내주식, 해외 ETF, 암호화폐, 금/은 선물까지 모두 Python으로 일별 시세 수집이 가능합니다.** ([GitHub][1])

필요하면 다음으로 **데이터를 DB(예: SQLite/MySQL/PostgreSQL)로 적재하는 자동화 파이프라인** 설계도 도와드릴까요? 😊

[1]: https://github.com/FinanceData/FinanceDataReader?utm_source=chatgpt.com "FinanceData/FinanceDataReader: Financial data reader"
