"""Deterministic in-view satellite selection used by the STK exporter."""
from __future__ import annotations


def select_satellite(
    candidates: list[dict],
    current_id: str | None,
    current_elevation_deg: float | None,
    acquire_elevation_deg: float,
    release_elevation_deg: float,
    dwell_elapsed_s: float,
    min_dwell_s: float,
) -> tuple[str | None, bool]:
    """Return (selected_id, switched).

    Candidates must contain ``id`` and ``elevation_deg`` and represent only
    satellites that are geometrically visible at the current epoch.  The
    current satellite is retained above the release mask.  Once below it,
    the highest candidate above the acquisition mask is selected, subject to
    the minimum dwell time.  No candidate yields ``None``.
    """
    eligible = [
        c for c in candidates
        if float(c["elevation_deg"]) >= float(acquire_elevation_deg)
    ]
    if current_id is not None and current_elevation_deg is not None:
        if float(current_elevation_deg) >= float(release_elevation_deg):
            return current_id, False
        if dwell_elapsed_s < min_dwell_s:
            return current_id, False
    if not eligible:
        return None, current_id is not None
    selected = max(eligible, key=lambda c: (float(c["elevation_deg"]), str(c["id"])))
    selected_id = str(selected["id"])
    return selected_id, selected_id != current_id
