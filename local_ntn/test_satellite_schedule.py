from local_ntn.satellite_schedule import select_satellite


def test_highest_candidate_is_selected_without_current():
    selected, switched = select_satellite(
        [{"id": "A", "elevation_deg": 12}, {"id": "B", "elevation_deg": 35}],
        None, None, 10, 5, 0, 0,
    )
    assert (selected, switched) == ("B", True)


def test_current_is_retained_above_release_mask():
    selected, switched = select_satellite(
        [{"id": "A", "elevation_deg": 12}, {"id": "B", "elevation_deg": 35}],
        "A", 8, 10, 5, 20, 0,
    )
    assert (selected, switched) == ("A", False)


def test_release_switch_and_no_candidate():
    selected, switched = select_satellite(
        [{"id": "B", "elevation_deg": 20}], "A", 2, 10, 5, 30, 0
    )
    assert (selected, switched) == ("B", True)
    selected, switched = select_satellite([], "B", 2, 10, 5, 30, 0)
    assert (selected, switched) == (None, True)


def test_minimum_dwell_prevents_immediate_ping_pong():
    selected, switched = select_satellite(
        [{"id": "B", "elevation_deg": 20}], "A", 2, 10, 5, 5, 30
    )
    assert (selected, switched) == ("A", False)
