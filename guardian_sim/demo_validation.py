"""Pure claim-boundary checks for presentation replays."""

from __future__ import annotations


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


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


def validate_gate32_replay_bundle(
    *,
    formal_report: dict[str, object],
    replay: dict[str, object],
) -> dict[str, object]:
    """Validate one visual replay against its frozen Gate 3.2 episode."""

    _require(
        replay.get("kind") == "gate32_visual_replay_not_formal_evidence",
        "unexpected replay kind",
    )
    protocol = formal_report["protocol"]
    _require(
        replay.get("formal_protocol_sha256") == protocol["protocol_sha256"],
        "formal protocol hash does not match replay",
    )
    seed = replay["seed"]
    formal_episode = next(
        (
            episode
            for episode in formal_report["episodes"]
            if episode["seed"] == seed
        ),
        None,
    )
    _require(formal_episode is not None, f"seed {seed} is absent from report")
    for field in (
        "scenario_id",
        "pick_object",
        "layout",
        "primary_obstacle",
    ):
        _require(
            replay[field] == formal_episode[field],
            f"{field} differs from formal episode",
        )

    formal_baseline = formal_episode["baseline"]
    formal_guardian = formal_episode["guardiansim"]
    replay_baseline = replay["visual_replay"]["baseline"]
    replay_guardian = replay["visual_replay"]["guardiansim"]
    _require(
        replay_baseline["candidate"]["candidate_id"]
        == formal_baseline["candidate"]["candidate_id"],
        "baseline candidate differs from formal episode",
    )
    _require(
        replay_guardian["candidate"]["candidate_id"]
        == formal_guardian["candidate"]["candidate_id"],
        "GuardianSim candidate differs from formal episode",
    )
    _require(
        formal_baseline["aggregate"]["execution_count"] == 3
        and formal_baseline["aggregate"]["clutter_contact_count"] == 3,
        "formal baseline is not the required three-contact case",
    )
    _require(
        formal_guardian["aggregate"]["execution_count"] == 3
        and formal_guardian["aggregate"]["safe_completion_count"] == 3,
        "formal GuardianSim result is not three-of-three safe",
    )
    _require(
        replay_retains_contact_to_safe_contrast(
            formal_baseline={
                "clutter_contact": (
                    formal_baseline["aggregate"]["clutter_contact_count"] > 0
                ),
                "safe_completion": formal_baseline["aggregate"][
                    "repeatable_safe_completion"
                ],
            },
            formal_guardian={
                "clutter_contact": (
                    formal_guardian["aggregate"]["clutter_contact_count"] > 0
                ),
                "safe_completion": formal_guardian["aggregate"][
                    "repeatable_safe_completion"
                ],
            },
            replay_baseline=replay_baseline["classification"],
            replay_guardian=replay_guardian["classification"],
        ),
        "replay does not retain formal contact-to-safe contrast",
    )

    baseline_metrics = replay_baseline["metrics"]
    guardian_metrics = replay_guardian["metrics"]
    baseline_diagnostic = baseline_metrics["clearance_diagnostic"]
    guardian_diagnostic = guardian_metrics["clearance_diagnostic"]
    _require(
        baseline_diagnostic["obstacle_name"] == replay["primary_obstacle"]
        and baseline_diagnostic["overlaps"]
        and baseline_diagnostic["overlap_depth_m"] > 0.0,
        "baseline replay lacks measured primary-obstacle overlap",
    )
    _require(
        guardian_diagnostic["obstacle_name"] == replay["primary_obstacle"]
        and not guardian_diagnostic["overlaps"]
        and guardian_metrics["collision_margin_m"] >= 0.01,
        "GuardianSim replay lacks at least 10 mm measured clearance",
    )

    return {
        "validated": True,
        "seed": seed,
        "scenario_id": replay["scenario_id"],
        "protocol_sha256": protocol["protocol_sha256"],
        "baseline_candidate_id": replay_baseline["candidate"]["candidate_id"],
        "guardian_candidate_id": replay_guardian["candidate"]["candidate_id"],
        "formal_baseline_contacts": formal_baseline["aggregate"][
            "clutter_contact_count"
        ],
        "formal_guardian_safe_executions": formal_guardian["aggregate"][
            "safe_completion_count"
        ],
        "replay_baseline_overlap_mm": (
            baseline_diagnostic["overlap_depth_m"] * 1000.0
        ),
        "replay_guardian_clearance_mm": (
            guardian_metrics["collision_margin_m"] * 1000.0
        ),
    }
