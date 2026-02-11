"""Discord webhook alerting for collection failures."""

import json
import logging
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


def send_discord_alert(webhook_url: str, message: str) -> bool:
    """Send a message to a Discord webhook.

    Args:
        webhook_url: Discord webhook URL. If empty, alert is skipped.
        message: Message text to send.

    Returns:
        True if sent successfully (or skipped), False on error.
        Never raises — alert failures must not disrupt the collection process.
    """
    if not webhook_url:
        logger.debug("Alert skipped: no webhook URL configured")
        return True

    try:
        payload = json.dumps({"content": message}).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            logger.info("Discord alert sent (status %d)", resp.status)
            return True
    except Exception as e:
        logger.warning("Discord alert failed: %s", e)
        return False


def format_failure_message(
    job_name: str,
    status: str,
    failures: list[dict],
) -> str:
    """Format a failure summary message for Discord.

    Args:
        job_name: Name of the job run.
        status: Final job status (e.g. "failure", "partial_failure").
        failures: List of dicts with asset_id, status, errors.

    Returns:
        Formatted message string.
    """
    lines = [
        f"**[Stock Dashboard] 수집 {status}**",
        f"Job: `{job_name}`",
        "",
    ]
    for f in failures[:10]:
        asset = f.get("asset_id", "?")
        errs = ", ".join(f.get("errors", [])[:2])
        lines.append(f"- {asset}: {errs}")

    if len(failures) > 10:
        lines.append(f"... 외 {len(failures) - 10}건")

    return "\n".join(lines)
