"""Category ordering shared by the per-run breakdown builders.

Single-API platforms use a fixed set of categories; multi-API platforms add
their own (reconciliation, onboarding, …). Rather than hardcode one list, the
breakdowns render the canonical single-API categories first — in their
established order, so single-API reports stay byte-identical — then append any
category present in the run's data but not in that prefix, in first-appearance
order.
"""
from __future__ import annotations

from collections.abc import Iterable

# Canonical ordering prefix: the single-API categories, in report order.
CANONICAL_CATEGORIES = [
    "retrieval", "search", "write", "workflow", "orchestration", "edge_case",
]


def resolve_categories(categories: Iterable[str | None]) -> list[str]:
    """Return the category buckets to render, canonical-first then appended.

    Accepts any iterable of category strings (callers pass the categories out
    of whatever per-prompt shape they hold). Falsy entries are ignored.
    """
    ordered = list(CANONICAL_CATEGORIES)
    seen = set(ordered)
    for cat in categories:
        if cat and cat not in seen:
            seen.add(cat)
            ordered.append(cat)
    return ordered
