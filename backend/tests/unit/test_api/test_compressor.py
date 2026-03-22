"""Tests for tool result compressor."""


from api.services.llm.agentic.compressor import (
    _compress_factors,
    _compress_prices,
    _compress_signals,
    compress_tool_results,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_price_rows(n: int = 365) -> list[dict]:
    """n일치 OHLCV 데이터 생성."""
    rows = []
    for i in range(n):
        day = f"2025-{(12 - i // 30) :02d}-{(28 - i % 28):02d}"
        rows.append({
            "date": day,
            "open": 50000 + i * 10,
            "high": 51000 + i * 10,
            "low": 49000 + i * 10,
            "close": 50500 + i * 10,
            "volume": 1000000 + i * 100,
        })
    return rows


def _make_factor_rows(n: int = 365) -> list[dict]:
    """n일치 팩터 데이터 생성 (rsi_14 + macd)."""
    rows = []
    for i in range(n):
        day = f"2025-{(12 - i // 30) :02d}-{(28 - i % 28):02d}"
        rows.append({
            "date": day, "asset_id": "005930",
            "factor_name": "rsi_14", "value": 50.0 + (i % 30),
        })
        rows.append({
            "date": day, "asset_id": "005930",
            "factor_name": "macd", "value": 100.0 - i * 0.5,
        })
    return rows


def _make_signal_rows(n: int = 365) -> list[dict]:
    """n일치 시그널 데이터 생성."""
    signals = ["buy", "sell", "hold"]
    rows = []
    for i in range(n):
        day = f"2025-{(12 - i // 30) :02d}-{(28 - i % 28):02d}"
        rows.append({
            "date": day, "asset_id": "005930",
            "strategy_id": "momentum",
            "signal": signals[i % 3],
            "score": 0.5 + (i % 10) * 0.05,
        })
    return rows


# ---------------------------------------------------------------------------
# compress_prices
# ---------------------------------------------------------------------------

class TestCompressPrices:
    def test_empty_rows(self):
        result = _compress_prices([])
        assert result == {"error": "no data"}

    def test_basic_compression(self):
        rows = _make_price_rows(365)
        result = _compress_prices(rows)

        assert result["total_days"] == 365
        assert len(result["recent_5_days"]) == 5
        assert "close_stats" in result
        assert "returns" in result
        assert result["close_stats"]["latest"] is not None

    def test_size_reduction(self):
        """압축 후 크기가 원본 대비 크게 줄어야 한다."""
        import json
        rows = _make_price_rows(365)
        original_size = len(json.dumps(rows))
        compressed_size = len(json.dumps(_compress_prices(rows)))

        # 최소 80% 감소
        assert compressed_size < original_size * 0.2, (
            f"압축 불충분: {original_size} → {compressed_size} "
            f"({compressed_size / original_size * 100:.0f}%)"
        )

    def test_returns_calculation(self):
        rows = _make_price_rows(30)
        result = _compress_prices(rows)
        assert result["returns"]["5d"] is not None
        assert result["returns"]["20d"] is not None
        # 30일 데이터로 250일 수익률은 None
        assert result["returns"]["250d"] is None


# ---------------------------------------------------------------------------
# compress_factors
# ---------------------------------------------------------------------------

class TestCompressFactors:
    def test_empty_rows(self):
        result = _compress_factors([])
        assert result == {"error": "no data"}

    def test_basic_compression(self):
        rows = _make_factor_rows(365)
        result = _compress_factors(rows)

        assert result["factor_count"] == 2
        assert "rsi_14" in result["factors"]
        assert "macd" in result["factors"]
        assert result["factors"]["rsi_14"]["latest_value"] is not None

    def test_size_reduction(self):
        import json
        rows = _make_factor_rows(365)
        original_size = len(json.dumps(rows))
        compressed_size = len(json.dumps(_compress_factors(rows)))

        assert compressed_size < original_size * 0.1, (
            f"압축 불충분: {original_size} → {compressed_size}"
        )

    def test_trend_calculation(self):
        rows = _make_factor_rows(60)
        result = _compress_factors(rows)
        rsi = result["factors"]["rsi_14"]
        assert "avg_30d" in rsi
        assert "trend_vs_30d" in rsi


# ---------------------------------------------------------------------------
# compress_signals
# ---------------------------------------------------------------------------

class TestCompressSignals:
    def test_empty_rows(self):
        result = _compress_signals([])
        assert result == {"error": "no data"}

    def test_basic_compression(self):
        rows = _make_signal_rows(365)
        result = _compress_signals(rows)

        assert result["total_signals"] == 365
        assert len(result["recent_10"]) == 10
        assert "summary" in result
        assert result["summary"]["buy_count"] > 0

    def test_by_strategy(self):
        rows = _make_signal_rows(30)
        result = _compress_signals(rows)
        assert "momentum" in result["by_strategy"]
        assert result["by_strategy"]["momentum"]["latest_signal"] is not None


# ---------------------------------------------------------------------------
# compress_tool_results (통합)
# ---------------------------------------------------------------------------

class TestCompressToolResults:
    def test_passthrough_unknown_tool(self):
        """알 수 없는 tool은 그대로 통과."""
        data = {"analyze_correlation_tool": {"groups": []}, "name_map": {"a": "b"}}
        result = compress_tool_results(data)
        assert result == data

    def test_mixed_compression(self):
        """압축 대상 + 비대상 tool 혼합."""
        data = {
            "get_prices": _make_price_rows(100),
            "analyze_indicators": {"states": "already_compact"},
            "name_map": {"005930": "삼성전자"},
        }
        result = compress_tool_results(data)

        # prices는 압축됨
        assert isinstance(result["get_prices"], dict)
        assert "recent_5_days" in result["get_prices"]
        # indicators는 그대로
        assert result["analyze_indicators"] == {"states": "already_compact"}
        # name_map 그대로
        assert result["name_map"] == {"005930": "삼성전자"}
