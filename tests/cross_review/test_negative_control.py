"""Aufgabe 6 — negative control: at least 2 of 3 reviewers must
detect the corruption."""
from __future__ import annotations

from ._helpers import load_corrupted


def test_corrupted_package_has_three_corruptions() -> None:
    c = load_corrupted()
    assert len(c["corruption_inventory"]) == 3


def test_at_least_two_reviewers_detect_each_corruption() -> None:
    c = load_corrupted()
    inventory_ids = {item["id"] for item in c["corruption_inventory"]}
    detect_counts: dict[str, int] = {cid: 0 for cid in inventory_ids}
    for rev in c["reviewers"]:
        for cid in rev["detections"]:
            if cid in detect_counts:
                detect_counts[cid] += 1
    missed = [cid for cid, n in detect_counts.items() if n < 2]
    assert not missed, (
        f"corruptions detected by fewer than 2 reviewers: {missed}"
    )


def test_at_least_two_of_three_reviewers_caught_majority() -> None:
    """Aufgabe 6: at least 2 of 3 reviewers must detect the
    corruption (interpreted as: each reviewer caught >= 2 of 3)."""
    c = load_corrupted()
    inv = len(c["corruption_inventory"])
    catchers = sum(
        1 for rev in c["reviewers"]
        if len(set(rev["detections"])) >= inv - 1
    )
    assert catchers >= 2


def test_no_reviewer_silently_passed_corrupted_package() -> None:
    c = load_corrupted()
    for rev in c["reviewers"]:
        assert rev["detections"], (
            f"{rev['reviewer_id']} returned zero detections — "
            "negative control silently passed"
        )


def test_every_detection_id_is_in_inventory() -> None:
    c = load_corrupted()
    inv_ids = {item["id"] for item in c["corruption_inventory"]}
    for rev in c["reviewers"]:
        for cid in rev["detections"]:
            assert cid in inv_ids, (
                f"{rev['reviewer_id']} claims detection {cid!r} "
                "which is not in the corruption inventory"
            )
