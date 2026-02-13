"""API integration tests — SQLite in-memory, full Router→Service→Repository pipeline.

Step 4.14 Part 2: Tests the entire API stack with a real (SQLite) database.
No mocks — actual DB reads/writes through repositories.
"""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from api.dependencies import get_db
from api.main import app
from db.models import (
    AssetMaster,
    Base,
    FactorDaily,
    PriceDaily,
    SignalDaily,
)

# ── SQLite in-memory setup ──
# StaticPool + check_same_thread=False: cross-thread usage for TestClient

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(TEST_ENGINE)
    yield
    Base.metadata.drop_all(TEST_ENGINE)


@pytest.fixture
def db_session():
    """Provide a session for seeding test data."""
    session = TestSession()
    yield session
    session.close()


@pytest.fixture
def client(db_session):
    """TestClient with real SQLite DB session injected."""

    def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def _seed_assets(db: Session):
    """Insert sample assets."""
    assets = [
        AssetMaster(
            asset_id="KS200", name="KOSPI200", category="index",
            source_priority={"primary": "fdr"}, is_active=True,
        ),
        AssetMaster(
            asset_id="005930", name="삼성전자", category="stock",
            source_priority={"primary": "fdr"}, is_active=True,
        ),
        AssetMaster(
            asset_id="BTC", name="비트코인", category="crypto",
            source_priority={"primary": "fdr"}, is_active=False,
        ),
    ]
    db.add_all(assets)
    db.flush()


def _seed_prices(db: Session, asset_id: str, base_close: float, n: int = 10):
    """Insert n days of price data."""
    for i in range(n):
        db.add(PriceDaily(
            asset_id=asset_id,
            date=date(2026, 1, n - i),
            source="fdr",
            open=base_close + i - 1,
            high=base_close + i + 1,
            low=base_close + i - 2,
            close=base_close + i,
            volume=10000 * (i + 1),
        ))
    db.flush()


def _seed_factors(db: Session, asset_id: str, n: int = 5):
    """Insert factor records."""
    for i in range(n):
        db.add(FactorDaily(
            asset_id=asset_id,
            date=date(2026, 1, n - i),
            factor_name="momentum_20d",
            version="v1",
            value=0.01 * (i + 1),
        ))
    db.flush()


def _seed_signals(db: Session, asset_id: str):
    """Insert signal records."""
    db.add(SignalDaily(
        asset_id=asset_id,
        date=date(2026, 1, 10),
        strategy_id="momentum",
        signal=1,
        action="buy",
    ))
    db.add(SignalDaily(
        asset_id=asset_id,
        date=date(2026, 1, 9),
        strategy_id="trend",
        signal=-1,
        action="sell",
    ))
    db.flush()


# ── Tests ──


class TestHealthIntegration:
    def test_health_connected(self, client):
        """Health endpoint reports connected with real SQLite DB."""
        resp = client.get("/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["db"] == "connected"


class TestAssetsIntegration:
    def test_list_assets(self, db_session, client):
        """Full pipeline: insert assets → GET /v1/assets → correct response."""
        _seed_assets(db_session)
        resp = client.get("/v1/assets")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        ids = {a["asset_id"] for a in data}
        assert ids == {"KS200", "005930", "BTC"}

    def test_filter_active(self, db_session, client):
        """Filter active assets through real DB."""
        _seed_assets(db_session)
        resp = client.get("/v1/assets?is_active=true")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(a["is_active"] for a in data)


class TestPricesIntegration:
    def test_list_prices(self, db_session, client):
        """Insert prices → GET /v1/prices/daily → paginated results."""
        _seed_assets(db_session)
        _seed_prices(db_session, "005930", 70000.0, n=10)

        resp = client.get("/v1/prices/daily?asset_id=005930")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 10
        # Ordered DESC by date
        assert data[0]["date"] >= data[-1]["date"]

    def test_date_filter(self, db_session, client):
        """Date range filter works through real DB."""
        _seed_assets(db_session)
        _seed_prices(db_session, "KS200", 300.0, n=10)

        resp = client.get(
            "/v1/prices/daily?asset_id=KS200&start_date=2026-01-05&end_date=2026-01-08"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all("2026-01-05" <= d["date"] <= "2026-01-08" for d in data)

    def test_pagination(self, db_session, client):
        """Pagination limit/offset works."""
        _seed_assets(db_session)
        _seed_prices(db_session, "005930", 70000.0, n=10)

        resp = client.get("/v1/prices/daily?asset_id=005930&limit=3&offset=2")
        assert resp.status_code == 200
        assert len(resp.json()) == 3


class TestFactorsIntegration:
    def test_list_factors(self, db_session, client):
        """Insert factors → GET /v1/factors → correct response."""
        _seed_assets(db_session)
        _seed_factors(db_session, "005930", n=5)

        resp = client.get("/v1/factors?asset_id=005930")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 5
        assert all(f["factor_name"] == "momentum_20d" for f in data)


class TestSignalsIntegration:
    def test_list_signals(self, db_session, client):
        """Insert signals → GET /v1/signals → correct response."""
        _seed_assets(db_session)
        _seed_signals(db_session, "005930")

        resp = client.get("/v1/signals?asset_id=005930")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2


class TestDashboardIntegration:
    def test_dashboard_summary(self, db_session, client):
        """Full dashboard pipeline: assets + prices + signals → summary."""
        _seed_assets(db_session)
        _seed_prices(db_session, "KS200", 300.0, n=5)
        _seed_prices(db_session, "005930", 70000.0, n=5)
        _seed_signals(db_session, "005930")

        resp = client.get("/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        # Only active assets (KS200, 005930) — BTC is inactive
        assert len(data["assets"]) == 2
        assert "updated_at" in data

        # Check an asset with prices has latest_price
        asset_map = {a["asset_id"]: a for a in data["assets"]}
        assert asset_map["KS200"]["latest_price"] is not None
        assert asset_map["005930"]["latest_price"] is not None


class TestCorrelationIntegration:
    def test_correlation_two_assets(self, db_session, client):
        """Full correlation pipeline with real price data."""
        _seed_assets(db_session)
        _seed_prices(db_session, "KS200", 300.0, n=20)
        _seed_prices(db_session, "005930", 70000.0, n=20)

        resp = client.get("/v1/correlation?asset_ids=KS200,005930&window=10")
        assert resp.status_code == 200
        data = resp.json()
        assert set(data["asset_ids"]) == {"KS200", "005930"}
        assert len(data["matrix"]) == 2
        assert len(data["matrix"][0]) == 2
        # Diagonal ≈ 1.0
        assert data["matrix"][0][0] == pytest.approx(1.0, abs=0.01)


class TestFullPipeline:
    def test_end_to_end_flow(self, db_session, client):
        """Scenario: health → assets → prices → factors → signals → dashboard → correlation."""
        # 1) Health
        assert client.get("/v1/health").status_code == 200

        # 2) Seed data
        _seed_assets(db_session)
        _seed_prices(db_session, "KS200", 300.0, n=15)
        _seed_prices(db_session, "005930", 70000.0, n=15)
        _seed_factors(db_session, "005930", n=5)
        _seed_signals(db_session, "005930")

        # 3) Assets
        resp = client.get("/v1/assets")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

        # 4) Prices
        resp = client.get("/v1/prices/daily?asset_id=005930&limit=5")
        assert resp.status_code == 200
        assert len(resp.json()) == 5

        # 5) Factors
        resp = client.get("/v1/factors?asset_id=005930&factor_name=momentum_20d")
        assert resp.status_code == 200
        assert len(resp.json()) == 5

        # 6) Signals
        resp = client.get("/v1/signals?asset_id=005930&strategy_id=momentum")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # 7) Dashboard
        resp = client.get("/v1/dashboard/summary")
        assert resp.status_code == 200
        assert len(resp.json()["assets"]) == 2  # active only

        # 8) Correlation
        resp = client.get("/v1/correlation?asset_ids=KS200,005930&window=10")
        assert resp.status_code == 200
        assert len(resp.json()["matrix"]) == 2
