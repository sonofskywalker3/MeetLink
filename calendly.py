"""Calendly API client."""

import logging
from dataclasses import dataclass

import requests

log = logging.getLogger(__name__)

API_BASE = "https://api.calendly.com"


@dataclass(frozen=True)
class EventType:
    uri: str
    name: str
    duration: int  # minutes
    active: bool


def get_current_user_uri(token: str) -> str:
    """Get the current user's Calendly URI."""
    resp = requests.get(
        f"{API_BASE}/users/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["resource"]["uri"]


def list_event_types(token: str, user_uri: str) -> list[EventType]:
    """List active event types for a user."""
    resp = requests.get(
        f"{API_BASE}/event_types",
        headers={"Authorization": f"Bearer {token}"},
        params={"user": user_uri, "active": "true"},
        timeout=10,
    )
    resp.raise_for_status()
    return [
        EventType(
            uri=et["uri"],
            name=et["name"],
            duration=et["duration"],
            active=et["active"],
        )
        for et in resp.json()["collection"]
    ]


def create_single_use_link(token: str, event_type_uri: str) -> str:
    """Create a single-use scheduling link for an event type."""
    resp = requests.post(
        f"{API_BASE}/scheduling_links",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "max_event_count": 1,
            "owner": event_type_uri,
            "owner_type": "EventType",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["resource"]["booking_url"]
