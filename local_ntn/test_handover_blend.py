import math

from local_ntn.handover_blend import interpolate_state, blend_alpha


def test_interpolate_state_is_continuous_between_satellites():
    old = {
        "position": [0.0, 100.0, 200.0],
        "velocity": [10.0, 20.0, 30.0],
        "acceleration": [1.0, 2.0, 3.0],
        "dl_power": -123.0,
        "ul_power": -119.0,
        "dl_cn": 17.0,
        "ul_cn": 11.0,
        "dl_valid": 1,
        "ul_valid": 1,
    }
    new = {
        "position": [100.0, 200.0, 300.0],
        "velocity": [-10.0, -20.0, -30.0],
        "acceleration": [-1.0, -2.0, -3.0],
        "dl_power": -121.0,
        "ul_power": -117.0,
        "dl_cn": 19.0,
        "ul_cn": 13.0,
        "dl_valid": 1,
        "ul_valid": 1,
    }
    assert interpolate_state(old, new, 0.0) == old
    assert interpolate_state(old, new, 1.0) == new
    middle = interpolate_state(old, new, 0.5)
    assert middle["position"] == [50.0, 150.0, 250.0]
    assert middle["velocity"] == [0.0, 0.0, 0.0]
    assert middle["dl_power"] == -122.0
    assert middle["ul_cn"] == 12.0


def test_blend_alpha_is_bounded_and_time_based():
    assert blend_alpha(100.0, 100.0, 5.0) == 0.0
    assert blend_alpha(102.0, 100.0, 5.0) == 0.4
    assert blend_alpha(110.0, 100.0, 5.0) == 1.0
    assert blend_alpha(90.0, 100.0, 5.0) == 0.0


def test_reference_site_interpolation_preserves_range_and_radial_velocity():
    old = {"position": [10.0, 0.0, 0.0], "velocity": [1.0, 0.0, 0.0],
           "acceleration": [0.0, 0.0, 0.0], "dl_power": -1.0,
           "ul_power": -1.0, "dl_cn": 1.0, "ul_cn": 1.0,
           "dl_valid": 1, "ul_valid": 1}
    new = {"position": [20.0, 0.0, 0.0], "velocity": [3.0, 0.0, 0.0],
           "acceleration": [0.0, 0.0, 0.0], "dl_power": -1.0,
           "ul_power": -1.0, "dl_cn": 1.0, "ul_cn": 1.0,
           "dl_valid": 1, "ul_valid": 1}
    middle = interpolate_state(old, new, 0.5, reference_site=[0.0, 0.0, 0.0])
    assert math.dist(middle["position"], [15.0, 0.0, 0.0]) == 0.0
    assert middle["velocity"][0] == 2.0
