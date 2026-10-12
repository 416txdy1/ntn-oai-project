"""Deterministic interpolation helpers for single-cell RFsim handovers."""

from __future__ import annotations

import math
from numbers import Real


_VECTOR_FIELDS = ("position", "velocity", "acceleration")
_SCALAR_FIELDS = ("dl_power", "ul_power", "dl_cn", "ul_cn")


def blend_alpha(time_s: float, start_s: float, duration_s: float) -> float:
    """Return a bounded blend factor for a monotonically increasing time."""
    if duration_s <= 0:
        return 1.0 if time_s >= start_s else 0.0
    value = (time_s - start_s) / duration_s
    return max(0.0, min(1.0, value))


def _lerp(old: Real, new: Real, alpha: float) -> float:
    return float(old) + (float(new) - float(old)) * alpha


def interpolate_state(old: dict, new: dict, alpha: float, reference_site=None) -> dict:
    """Interpolate a trace state and optionally preserve range continuity."""
    alpha = max(0.0, min(1.0, float(alpha)))
    result = dict(old)
    for field in _VECTOR_FIELDS:
        result[field] = [_lerp(a, b, alpha) for a, b in zip(old[field], new[field])]
    for field in _SCALAR_FIELDS:
        result[field] = _lerp(old[field], new[field], alpha)
    if reference_site is not None:
        old_rel = [a - b for a, b in zip(old["position"], reference_site)]
        new_rel = [a - b for a, b in zip(new["position"], reference_site)]
        old_range = math.sqrt(sum(value * value for value in old_rel))
        new_range = math.sqrt(sum(value * value for value in new_rel))
        if old_range > 0.0 and new_range > 0.0:
            direction = [_lerp(a / old_range, b / new_range, alpha)
                         for a, b in zip(old_rel, new_rel)]
            direction_norm = math.sqrt(sum(value * value for value in direction))
            direction = [value / direction_norm for value in direction]
            target_range = _lerp(old_range, new_range, alpha)
            result["position"] = [site + target_range * unit
                                   for site, unit in zip(reference_site, direction)]
            old_radial = sum(a * b for a, b in zip(old_rel, old["velocity"])) / old_range
            new_radial = sum(a * b for a, b in zip(new_rel, new["velocity"])) / new_range
            target_radial = _lerp(old_radial, new_radial, alpha)
            velocity = result["velocity"]
            correction = target_radial - sum(a * b for a, b in zip(velocity, direction))
            result["velocity"] = [value + correction * unit
                                   for value, unit in zip(velocity, direction)]
    result["dl_valid"] = int(bool(old.get("dl_valid", 0)) and bool(new.get("dl_valid", 0)))
    result["ul_valid"] = int(bool(old.get("ul_valid", 0)) and bool(new.get("ul_valid", 0)))
    return result
