"""Calendly API client."""

import json
import logging
from dataclasses import dataclass

import requests

log = logging.getLogger(__name__)

API_BASE = "https://api.calendly.com"


@dataclass(frozen=True)
class UserInfo:
    uri: str
    timezone: str


@dataclass(frozen=True)
class EventType:
    uri: str
    name: str
    duration: int  # default duration in minutes
    duration_options: tuple[int, ...] | None  # multi-duration choices, None if single
    active: bool


def get_current_user(token: str) -> UserInfo:
    """Get the current user's URI and timezone."""
    resp = requests.get(
        f"{API_BASE}/users/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    resource = resp.json()["resource"]
    return UserInfo(uri=resource["uri"], timezone=resource["timezone"])


def list_event_types(token: str, user_uri: str) -> list[EventType]:
    """List active event types for a user."""
    resp = requests.get(
        f"{API_BASE}/event_types",
        headers={"Authorization": f"Bearer {token}"},
        params={"user": user_uri, "active": "true"},
        timeout=10,
    )
    resp.raise_for_status()
    result = []
    for et in resp.json()["collection"]:
        raw_options = et.get("duration_options")
        duration_options = tuple(sorted(raw_options)) if raw_options else None
        result.append(
            EventType(
                uri=et["uri"],
                name=et["name"],
                duration=et["duration"],
                duration_options=duration_options,
                active=et["active"],
            )
        )
    return result


def create_single_use_link(
    token: str,
    event_type_uri: str,
    overrides: dict | None = None,
) -> str:
    """Create a single-use scheduling link via POST /shares.

    Overrides (duration, duration_options, availability_rule, etc.)
    go at the top level of the request body alongside event_type.
    """
    body: dict = {"event_type": event_type_uri}
    if overrides:
        body.update(overrides)

    log.info("POST /shares body: %s", json.dumps(body, indent=2))

    resp = requests.post(
        f"{API_BASE}/shares",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=10,
    )
    log.info("Response %s: %s", resp.status_code, resp.text[:500])
    resp.raise_for_status()
    return resp.json()["resource"]["scheduling_links"][0]["booking_url"]
