"""Unit tests for collector.alerting — Discord webhook alerts."""

from unittest.mock import MagicMock, patch

from collector.alerting import format_failure_message, send_discord_alert


class TestSendDiscordAlert:
    def test_success(self):
        """Alert sends successfully via urllib and returns True."""
        mock_resp = MagicMock()
        mock_resp.status = 204
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        url_patch = "collector.alerting.urllib.request.urlopen"
        with patch(url_patch, return_value=mock_resp) as mock_open:
            result = send_discord_alert("https://discord.com/api/webhooks/test", "hello")

        assert result is True
        mock_open.assert_called_once()

    def test_skipped_when_no_webhook(self):
        """Empty webhook URL skips sending and returns True."""
        with patch("collector.alerting.urllib.request.urlopen") as mock_open:
            result = send_discord_alert("", "hello")

        assert result is True
        mock_open.assert_not_called()

    def test_failure_does_not_raise(self):
        """Alert failure returns False but never raises."""
        with patch(
            "collector.alerting.urllib.request.urlopen",
            side_effect=Exception("network error"),
        ):
            result = send_discord_alert("https://discord.com/api/webhooks/test", "hello")

        assert result is False


class TestFormatFailureMessage:
    def test_format_basic(self):
        failures = [
            {"asset_id": "005930", "status": "fetch_failed", "errors": ["timeout"]},
            {"asset_id": "BTC", "status": "validation_failed", "errors": ["empty df"]},
        ]
        msg = format_failure_message(
            "ingest_all(2026-02-01~2026-02-11)", "partial_failure", failures
        )

        assert "partial_failure" in msg
        assert "005930" in msg
        assert "BTC" in msg
        assert "timeout" in msg

    def test_format_truncates_long_list(self):
        failures = [{"asset_id": f"A{i}", "errors": ["err"]} for i in range(15)]
        msg = format_failure_message("job", "failure", failures)

        assert "외 5건" in msg
