"""Pure claim-boundary checks for presentation replays."""

from __future__ import annotations


def replay_retains_contact_to_safe_contrast(
    *,
    formal_baseline: dict[str, object],
    formal_guardian: dict[str, object],
    replay_baseline: dict[str, object],
    replay_guardian: dict[str, object],
) -> bool:
    """Return whether a fresh replay retains the verified presentation case."""

    return bool(
        formal_baseline["clutter_contact"]
        and not formal_baseline["safe_completion"]
        and formal_guardian["safe_completion"]
        and not formal_guardian["clutter_contact"]
        and replay_baseline["clutter_contact"]
        and not replay_baseline["safe_completion"]
        and replay_guardian["safe_completion"]
        and not replay_guardian["clutter_contact"]
    )
