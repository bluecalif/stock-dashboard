아래는 **한국투자증권(KIS Developers)의 Open API (REST/WebSocket)** 를 이용해,
당신이 프로젝트에서 필요한 **다음 7개 자산**의 가격/시세 데이터를 수집하는 방법에 대한 정리입니다:

📌 **수집 대상 자산**

* **KOSPI200 지수**
* **삼성전자 주가**
* **SK하이닉스 주가**
* **SOXL ETF 주가**
* **비트코인 가격**
* **금 선물 지수**
* **은 선물 지수**

> 참고: **한국투자증권 Open API는 REST(WebSocket 포함) 기반으로 국내/해외 시세 및 주문/잔고 등 다양한 기능을 제공합니다.** ([한국투자증권 API 포털][1])

---

## 🧩 전체 흐름 개요

1. **API 신청 및 인증**

   * 한국투자증권 Open API 서비스 신청 → 앱키(App Key) + 앱 Secret 발급 ([한국투자증권 API 포털][2])
2. **토큰 발급 (Access Token)**
3. **REST API 호출을 통해 시세 조회**

   * 국내주식, 해외주식, ETF 등 기본 시세 조회
4. **수집 데이터를 DB에 저장 및 후 처리**

---

## 1) Open API 신청 및 인증 토큰 발급

### ✔ API 신청

* 한국투자증권 개발자 포털(KIS Developers)에서 API 사용을 신청합니다.
* 계좌 정보 입력 후 **App Key, App Secret**을 발급받습니다. ([한국투자증권 API 포털][2])

### ✔ 토큰 발급

한국투자증권 API는 **OAuth2** 기반 인증이며, 토큰을 발급받아 호출 시 헤더로 전달해야 합니다.

```python
import requests

API_KEY = "YOUR_APP_KEY"
API_SECRET = "YOUR_APP_SECRET"

url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
headers = {
    "content-type": "application/json"
}
payload = {
    "grant_type": "client_credentials",
    "appkey": API_KEY,
    "appsecret": API_SECRET
}

response = requests.post(url, headers=headers, json=payload)
access_token = response.json().get("access_token")
```

* 이 `access_token`을 헤더에 넣어 모든 REST 호출을 수행합니다.

---

## 2) 국내주식(삼전, 하이닉스) 일별 시세 수집

KIS REST API에서 **국내주식 기본 시세**를 제공하는 엔드포인트가 있습니다. ([한국투자증권 API 포털][3])

### ✔ 기본 주식 시세 조회

```python
import requests

BASE_URL = "https://openapi.koreainvestment.com:9443"
TOKEN = access_token

headers = {
    "authorization": f"Bearer {TOKEN}",
    "appkey": API_KEY,
    "appsecret": API_SECRET,
    "content-type": "application/json"
}

params = {
    "FID_COND_MRKT_DIV_CODE": "J",  # 국내주식
    "FID_INPUT_ISCD": "005930"     # 삼성전자 종목코드
}

url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
response = requests.get(url, headers=headers, params=params)
data = response.json()
print(data)
```

* `FID_INPUT_ISCD`에 **종목 코드**(삼전=005930, 하이닉스=000660)를 넣어 호출합니다.

### ✔ 일별 시세(히스토리)

일별 차트(OHLCV) 데이터는 **차트형 시세 조회 API**를 사용해야 합니다.
한국투자 Open API 문서 내 “국내주식 시세 분석/차트” 관련 항목이 존재합니다 (포털에서 검색 후 API Path 확인 필요). ([한국투자증권 API 포털][1])

---

## 3) 해외 ETF (SOXL) 시세 수집

해외 주식/ETF는 한국투자증권의 **해외주식 기본 시세 엔드포인트**를 통해 조회가 가능합니다.

```python
params = {
    "FID_INPUT_ISCD": "SOXL",  # 미국 ETF 코드
    "FID_INPUT_OTC_CD": "NA"   # 나스닥, NYSE 등 시장 코드
}

url = f"{BASE_URL}/uapi/overseas-stock/v1/quotations/inquire-price"
response = requests.get(url, headers=headers, params=params)
data = response.json()
```

* **해외 ETF** 시세 조회도 국내주식과 유사하게 API를 사용합니다.

---

## 4) KOSPI200 지수 수집

한국투자 API는 **지수 자체**를 직접 제공하는 엔드포인트를 포함합니다.
예: 국내주식 지수/업종/지표 시세 API → KOSPI 200 지수 일별 시세 조회 가능.

```python
params = {
    "FID_INPUT_INDICATOR_CODE": "200"   # KOSPI200 지수 코드 (예)
}

url = f"{BASE_URL}/uapi/marketindex/v1/quotations/inquire-index-price"
response = requests.get(url, headers=headers, params=params)
```

> 정확한 파라미터명과 코드값은 API 문서 검색 기능을 통해 조회 가능하며, 기본 제공되는 종목 정보 마스터 파일을 통해 종목 및 지수 코드 전체를 확보합니다. ([한국투자증권 API 포털][1])

---

## 5) 비트코인 가격(암호화폐)

한국투자 API는 **암호화폐 시세** 자체를 기본 제공하지 않습니다.
→ 비트코인의 경우 ** 외부 API**(예: CoinGecko/FinanceDataReader/거래소 REST API)와 결합하여 수집하는 것이 일반적입니다.

👉 한국투자 API는 증권/주식/ETF/선물 옵션 중심이며 암호화폐 DB는 지원되지 않음을 유념해야 합니다.

---

## 6) 금/은 선물 시세 수집

한국투자 API는 국내/해외 **선물/옵션 시세** 엔드포인트를 갖고 있습니다. ([한국투자증권 API 포털][1])

예를 들어 “해외선물옵션 기본 시세” API를 호출하여 금/은 선물의 OHLCV를 조회할 수 있습니다.

```python
params = {
    # 종목 구분 및 코드 설정 (금 선물/은 선물)
    "FID_INPUT_ISCD": "GC=F"
}

url = f"{BASE_URL}/uapi/overseas-futureoption/v1/quotations/inquire-price"
response = requests.get(url, headers=headers, params=params)
```

* 금/은 선물도 해외선물옵션 API 카테고리로 제공됩니다.

---

## 🧪 실전 수집 팁

### ✔ 종목 마스터 조회

한국투자 Open API는 전체 종목 마스터를 REST로 제공합니다.
이를 통해 **국내/해외 종목 코드, 선물/지수 코드**를 먼저 확보하는 것이 실전 수집의 기본입니다. ([한국투자증권 API 포털][1])

### ✔ 토큰 유효기간

OpenAPI의 토큰은 일정 시간만 유효하므로 **서버에서 자동 재발급 로직**을 구현해야 합니다.

---

## 📌 요약

| 자산                | 한국투자 API 수집 가능 여부         |
| ----------------- | ------------------------- |
| **KOSPI200 지수**   | 가능 (지수 시세 API)            |
| **삼성전자, 하이닉스 주가** | 가능 (국내주식 시세 API)          |
| **SOXL ETF 주가**   | 가능 (해외주식 시세 API)          |
| **비트코인 가격**       | *불가* (한국투자 API는 암호화폐 비지원) |
| **금/은 선물 지수**     | 가능 (해외선물옵션 시세 API)        |

---

## 📌 전체 파이썬 REST 수집 예시 템플릿 (요약)

```python
import requests

ACCESS_TOKEN = get_token(API_KEY, API_SECRET)  # 앞서 토큰 발급 함수

def fetch_price(endpoint, params):
    headers = {
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": API_KEY,
        "appsecret": API_SECRET,
        "content-type": "application/json"
    }
    url = f"https://openapi.koreainvestment.com:9443{endpoint}"
    return requests.get(url, headers=headers, params=params).json()

# 국내주식
fetch_price("/uapi/domestic-stock/v1/quotations/inquire-price",
            {"FID_COND_MRKT_DIV_CODE":"J","FID_INPUT_ISCD":"005930"})
```

---

## 📎 참고

* 한국투자증권 Open API 공식 개발자 포털에서 문서/엔드포인트를 검색해 정확한 Name/Path를 확인하며 구현하세요. ([한국투자증권 API 포털][1])

---

원하면 **구체적인 코드 베이스(실행 가능한 REST 호출 + 토큰 자동 갱신 포함)** 템플릿도 단계별로 정리해 드릴까요? (자동 수집 + DB 적재까지) 😊

[1]: https://apiportal.koreainvestment.com/apiservice?utm_source=chatgpt.com "KIS Developers : 한국투자증권 오픈API 개발자센터"
[2]: https://apiportal.koreainvestment.com/?utm_source=chatgpt.com "KIS Developers : 한국투자증권 오픈API 개발자센터"
[3]: https://apiportal.koreainvestment.com/apiservice-apiservice?%2Fuapi%2Fdomestic-stock%2Fv1%2Fquotations%2Finquire-price=&utm_source=chatgpt.com "REST주식현재가 시세[v1_국내주식-008]"
