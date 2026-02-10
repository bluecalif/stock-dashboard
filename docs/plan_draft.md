## 📌 최종 보완된 프로젝트 계획

---

### 🎯 1. 프로젝트 개요

**프로젝트 목표**

* KOSPI200 지수를 중심으로 7개 자산의 트렌드 분석을 수행
* 예측 모델 기반 매수/매도 시점을 사용자에게 제안하는 프로그램 구현

**대상 지표**

1. KOSPI200 지수
2. 삼성전자 주가
3. SK하이닉스 주가
4. SOXL ETF 주가
5. 금 선물 지수
6. 은 선물 지수
7. 비트코인 가격

---

## 🗂 2. 데이터 수집 전략

### 📌 2-1. 주요 데이터 소스 비교

| 자산군            | 데이터 소스                         | 방식       | 주기  | 인증    |
| -------------- | ------------------------------ | -------- | --- | ----- |
| 국내주식(삼전, 하이닉스) | FinanceDataReader / 키움 OpenAPI | API/스크래핑 | 영업일 | 키움 필요 |
| KOSPI200 (지수)  | FinanceDataReader              | API      | 영업일 | 없음    |
| SOXL ETF       | FinanceDataReader              | API      | 영업일 | 없음    |
| 비트코인           | FinanceDataReader              | API      | 1일  | 없음    |
| 금/은 선물         | FinanceDataReader (COMEX)      | API      | 1일  | 없음    |

---

### 📌 2-2. 수집 방법 상세

#### ➤ 1) **FinanceDataReader (FDR) 기반**

* Python 라이브러리 설치

```bash
pip install finance-datareader
```

* 주요 예시 코드

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
```

**장점**

* 설치/구현이 간편
* 다양한 시장/자산 지원
* Pandas DataFrame으로 수집

**단점**

* 일부 자산 소스 정책 변동 시 영향
* 금/은 선물은 실제 월물 계약과 차이가 있을 수 있음

---

#### ➤ 2) **키움증권 OpenAPI+ 기반(국내주식 보완)**

Windows + Python 환경에서 국내주식의 **정밀한 일별 데이터를 수집**하기 위한 방법입니다.

* 설치 요구조건

  * 키움증권 계정
  * OpenAPI+ 설치 (ActiveX)
  * Python + PyQt5

* 일봉 수집 TR

  * `OPT10081 (주식일봉차트조회)`

```python
from pykiwoom.kiwoom import Kiwoom

kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)
```

---

## 📊 3. 데이터 저장 구조 (DB 설계)

### 📌 3-1. 테이블 설계

#### 📌 (1) asset_master

| 컬럼       | 타입   | 설명                           |
| -------- | ---- | ---------------------------- |
| asset_id | TEXT | 종목 식별키                       |
| name     | TEXT | 자산명                          |
| type     | TEXT | stock/index/crypto/commodity |

#### 📌 (2) price_daily

| 컬럼       | 타입         | 설명              |
| -------- | ---------- | --------------- |
| id       | INTEGER PK | 레코드 식별          |
| asset_id | TEXT FK    | asset_master 참조 |
| date     | DATE       | 거래일             |
| open     | REAL       | 시가              |
| high     | REAL       | 고가              |
| low      | REAL       | 저가              |
| close    | REAL       | 종가              |
| volume   | INTEGER    | 거래량             |

---

## 📈 4. 분석 파이프라인

### 📌 4-1. 전처리

* 결측값 처리 (forward/backfill)
* 거래일 기준으로 join
* log return / rolling 통계 생성

---

### 📌 4-2. 상관관계/인과관계 분석

사용 지표 간 상관계수 분석

```python
df_returns.corr()
```

인과관계는 Granger Causality 등으로 분석

---

## 📈 5. 예측 모델링

### ✔ 선택 모델 예시

| 유형      | 알고리즘                  |
| ------- | --------------------- |
| 시계열     | ARIMA, Prophet        |
| 회귀/머신러닝 | RandomForest, XGBoost |
| 딥러닝     | LSTM                  |

> KOSPI200 기준으로 멀티변수 입력/교차검증

---

## 📊 6. 대시보드 & 시뮬레이션

### 📌 6-1. 대시보드 항목

✔ 실시간 업데이트된 가격 차트
✔ 과거 7개 지표 비교 차트
✔ 상관관계 히트맵
✔ 예측 결과와 매수/매도 시점 제안

---

### 📌 6-2. 수익률 시뮬레이션

* 입력: 투자 시작일, 종료일, 금액
* 출력: 포트폴리오 수익률 비교

---

## ⚙️ 7. 자동화 및 운영

| 구성요소                   | 역할              |
| ---------------------- | --------------- |
| Airflow                | 주기 데이터 파이프라인    |
| SQLite/PostgreSQL      | 시세 저장           |
| Windows Task Scheduler | 키움 OpenAPI 스케줄러 |
| Git/GitHub             | 버전 관리           |

---

## 🧪 8. 테스트 & 검증

✔ 샘플 데이터로 백테스트
✔ 예측 성능 측정(MAPE/RMSE)
✔ 지표 간 인과성 확인

---

## 📌 9. 우선순위 & 일정 (예시)

| 단계         | 기간 |
| ---------- | -- |
| 환경 구축      | 2일 |
| 데이터 수집 자동화 | 4일 |
| 분석/인과관계정의  | 3일 |
| 예측 모델 개발   | 5일 |
| UI/대시보드    | 4일 |
| 시뮬레이션 모듈   | 2일 |
| 통합 테스팅     | 3일 |

---

## 📌 10. 확장 가능성

✔ 해외 ETF 추가
✔ 분/틱 데이터 추가
✔ 머신러닝 실시간 알림

---

## 📌 결론

위 계획은 **수집 → 저장 → 분석 → 예측 → UX**로 이어지는 전체적인 파이프라인을 고려합니다.
특히 **FinanceDataReader + 키움 OpenAPI**를 혼합해 안정성/정확도를 확보하는 구성입니다.

---

필요하면 **구체적인 코드 템플릿(수집/DB 적재/예측/대시보드)**도 단계별로 드릴까요? 😊
