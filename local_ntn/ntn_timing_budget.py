"""Nominal mu=0 RFsim scheduling budget; not a bound on actual TX writes."""
import math
import re

def cell_koffset_ms(profile, environ):
    if profile == 'zky':
        return None
    value = environ.get('OAI_NTN_CELL_KOFFSET_MS')
    if value is None or value == '':
        return None
    if not re.fullmatch(r'[0-9]{1,4}', value) or not 1 <= int(value) <= 1023:
        raise ValueError('OAI_NTN_CELL_KOFFSET_MS must be an integer from 1 to 1023')
    return int(value)

def timing_budget(rows, koffset, interpolation):
    if interpolation != 'legacy-linear':
        raise ValueError('K-offset budget requires legacy-linear interpolation')
    # Both sites and the satellite interpolate affinely. Sum of distances is
    # convex on each segment, so its maximum is bounded by the two endpoints.
    maximum = max(2 * (math.dist(v[1:4], v[10:13]) +
                       math.dist(v[1:4], v[13:16])) / 299792458 * 1000 for v in rows)
    lead = 3 + koffset - maximum
    result = {'cell_koffset_ms': koffset, 'numerology': 0,
              'max_geometric_roundtrip_ms': maximum,
              'nominal_write_lead_ms': lead, 'required_nominal_lead_ms': 5,
              'minimum_integer_koffset_ms': math.ceil(maximum + 5 - 3),
              'qualification': 'nominal only; excludes ordinary TA, NTA and prediction error'}
    if lead < 5:
        raise ValueError('K-offset nominal write lead below 5 ms: %.6f ms' % lead)
    return result
