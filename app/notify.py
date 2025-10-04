import os
import logging
from typing import Any, Dict

import requests

from app import crud

logger = logging.getLogger(__name__)

def send_stats_to_notification(url: str, stats: Dict[str, Any]) -> requests.Response:
    payload = {
        "event": "subscription_stats",
        "stats": {
            "total": stats["total"],
            "total_active": stats["total_active"],
            "by_plan": stats["by_plan"],
            "by_status": stats["by_status"],
            # ISO format for JSON-friendly timestamp
            "generated_at": stats["generated_at"].isoformat() + "Z"
        }
    }
    resp = requests.post(url, json=payload, timeout=5)
    resp.raise_for_status()
    return resp

def notify_counts() -> requests.Response:
    url = os.environ.get("NOTIFICATION_URL")
    if not url:
        raise RuntimeError("NOTIFICATION_URL environment variable is not set")
    stats = crud.get_subscription_stats()
    return send_stats_to_notification(url, stats)
