"""Pydantic 스키마 단위 테스트."""

import datetime
from uuid import UUID, uuid4

from api.schemas import (
    AssetResponse,
    AssetSummary,
    BacktestRunRequest,
    BacktestRunResponse,
    CorrelationPeriod,
    CorrelationResponse,
    DashboardSummaryResponse,
    EquityCurveResponse,
    ErrorResponse,
    FactorDailyResponse,
    PaginationParams,
    PriceDailyResponse,
    SignalDailyResponse,
    TradeLogResponse,
)

# ── PaginationParams ──


class TestPaginationParams:
    def test_defaults(self):
        """FastAPI DI 외부에서는 Query 객체가 기본값이므로 직접 값 전달 테스트."""
        p = PaginationParams(limit=500, offset=0)
        assert p.limit == 500
        assert p.offset == 0

    def test_custom_values(self):
        p = PaginationParams(limit=100, offset=50)
        assert p.limit == 100
        assert p.offset == 50


# ── ErrorResponse ──


class TestErrorResponse:
    def test_create(self):
        e = ErrorResponse(detail="Not found", error_code="NOT_FOUND")
        assert e.detail == "Not found"
        assert e.error_code == "NOT_FOUND"

    def test_json_round_trip(self):
        e = ErrorResponse(detail="err", error_code="CODE")
        data = e.model_dump()
        assert data == {"detail": "err", "error_code": "CODE"}


# ── AssetResponse ──


class TestAssetResponse:
    def test_from_dict(self):
        a = AssetResponse(
            asset_id="005930", name="삼성전자", category="stock", is_active=True
        )
        assert a.asset_id == "005930"
        assert a.name == "삼성전자"

    def test_from_attributes(self):
        """from_attributes=True — ORM 객체처럼 속성 접근 가능한 객체에서 생성."""

        class FakeORM:
            asset_id = "KS200"
            name = "KOSPI200"
            category = "index"
            is_active = True

        a = AssetResponse.model_validate(FakeORM())
        assert a.asset_id == "KS200"


# ── PriceDailyResponse ──


class TestPriceDailyResponse:
    def test_create(self):
        p = PriceDailyResponse(
            asset_id="005930",
            date=datetime.date(2026, 1, 15),
            open=70000.0,
            high=71000.0,
            low=69500.0,
            close=70500.0,
            volume=15000000,
            source="fdr",
        )
        assert p.close == 70500.0
        assert p.volume == 15000000

    def test_date_serialization(self):
        p = PriceDailyResponse(
            asset_id="KS200",
            date=datetime.date(2026, 2, 1),
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.5,
            volume=0,
            source="fdr",
        )
        data = p.model_dump(mode="json")
        assert data["date"] == "2026-02-01"


# ── FactorDailyResponse ──


class TestFactorDailyResponse:
    def test_create(self):
        f = FactorDailyResponse(
            asset_id="005930",
            date=datetime.date(2026, 1, 10),
            factor_name="rsi_14",
            version="1.0",
            value=55.3,
        )
        assert f.factor_name == "rsi_14"
        assert f.value == 55.3


# ── SignalDailyResponse ──


class TestSignalDailyResponse:
    def test_full(self):
        s = SignalDailyResponse(
            id=1,
            asset_id="005930",
            date=datetime.date(2026, 1, 20),
            strategy_id="momentum",
            signal=1,
            score=0.85,
            action="BUY",
            meta_json={"threshold": 0.5},
        )
        assert s.action == "BUY"
        assert s.meta_json == {"threshold": 0.5}

    def test_optional_fields_none(self):
        s = SignalDailyResponse(
            id=2,
            asset_id="KS200",
            date=datetime.date(2026, 1, 21),
            strategy_id="trend",
            signal=0,
        )
        assert s.score is None
        assert s.action is None
        assert s.meta_json is None


# ── BacktestRunRequest ──


class TestBacktestRunRequest:
    def test_defaults(self):
        r = BacktestRunRequest(strategy_id="momentum", asset_id="005930")
        assert r.initial_cash == 10_000_000
        assert r.commission_pct == 0.001
        assert r.start_date is None
        assert r.end_date is None

    def test_custom(self):
        r = BacktestRunRequest(
            strategy_id="trend",
            asset_id="KS200",
            start_date=datetime.date(2025, 1, 1),
            end_date=datetime.date(2025, 12, 31),
            initial_cash=5_000_000,
            commission_pct=0.002,
        )
        assert r.start_date == datetime.date(2025, 1, 1)
        assert r.initial_cash == 5_000_000


# ── BacktestRunResponse ──


class TestBacktestRunResponse:
    def test_create(self):
        run_id = uuid4()
        r = BacktestRunResponse(
            run_id=run_id,
            strategy_id="momentum",
            asset_id="005930",
            status="completed",
            config_json={"initial_cash": 10_000_000},
            metrics_json={"total_return": 0.12},
            started_at=datetime.datetime(2026, 1, 1, 9, 0, tzinfo=datetime.timezone.utc),
            ended_at=datetime.datetime(2026, 1, 1, 9, 0, 5, tzinfo=datetime.timezone.utc),
        )
        assert isinstance(r.run_id, UUID)
        assert r.status == "completed"

    def test_uuid_serialization(self):
        run_id = uuid4()
        r = BacktestRunResponse(
            run_id=run_id,
            strategy_id="trend",
            asset_id="KS200",
            status="running",
            config_json={},
            started_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        )
        data = r.model_dump(mode="json")
        assert data["run_id"] == str(run_id)


# ── EquityCurveResponse ──


class TestEquityCurveResponse:
    def test_create(self):
        e = EquityCurveResponse(
            run_id=uuid4(),
            date=datetime.date(2026, 1, 15),
            equity=10_500_000.0,
            drawdown=-0.02,
        )
        assert e.equity == 10_500_000.0
        assert e.drawdown == -0.02


# ── TradeLogResponse ──


class TestTradeLogResponse:
    def test_full(self):
        t = TradeLogResponse(
            id=1,
            run_id=uuid4(),
            asset_id="005930",
            entry_date=datetime.date(2026, 1, 10),
            entry_price=70000.0,
            exit_date=datetime.date(2026, 1, 20),
            exit_price=72000.0,
            side="long",
            shares=100.0,
            pnl=200000.0,
            cost=144.0,
        )
        assert t.pnl == 200000.0

    def test_open_trade(self):
        t = TradeLogResponse(
            id=2,
            run_id=uuid4(),
            asset_id="KS200",
            entry_date=datetime.date(2026, 2, 1),
            entry_price=350.0,
            side="long",
            shares=50.0,
        )
        assert t.exit_date is None
        assert t.pnl is None


# ── CorrelationResponse ──


class TestCorrelationResponse:
    def test_create(self):
        c = CorrelationResponse(
            asset_ids=["KS200", "005930", "SOXL"],
            matrix=[[1.0, 0.8, 0.3], [0.8, 1.0, 0.4], [0.3, 0.4, 1.0]],
            period=CorrelationPeriod(
                start=datetime.date(2025, 1, 1),
                end=datetime.date(2025, 12, 31),
                window=60,
            ),
        )
        assert len(c.matrix) == 3
        assert c.period.window == 60


# ── DashboardSummaryResponse ──


class TestDashboardSummaryResponse:
    def test_create(self):
        d = DashboardSummaryResponse(
            assets=[
                AssetSummary(
                    asset_id="005930",
                    name="삼성전자",
                    latest_price=70500.0,
                    price_change_pct=1.5,
                    latest_signal={"momentum": "BUY"},
                ),
                AssetSummary(
                    asset_id="KS200",
                    name="KOSPI200",
                ),
            ],
            recent_backtests=[],
            updated_at=datetime.datetime(2026, 2, 12, 10, 0, tzinfo=datetime.timezone.utc),
        )
        assert len(d.assets) == 2
        assert d.assets[0].latest_signal == {"momentum": "BUY"}
        assert d.assets[1].latest_price is None
