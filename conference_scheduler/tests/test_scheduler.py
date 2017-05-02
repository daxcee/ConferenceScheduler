import numpy as np
from collections import Counter
from conference_scheduler import scheduler


def test_is_valid_ssolution():
    talks, slots = 2, 3

    # a valid solution with one talk per slot
    X = np.array([
        [1, 0, 0],
        [0, 1, 0]
    ])
    # a list of constraints specifying that a slot may have at most one talk
    constraints = (
        sum(X[(talk, slot)] for talk in range(talks)) <= 1
        for slot in range(slots)
    )
    assert scheduler.is_valid_solution(X, constraints)

    # An invalid solution with 2 talks scheduled in slot 1
    X = np.array([
        [1, 0, 0],
        [1, 0, 0]
    ])
    # a list of constraints specifying that a slot may have at most one talk
    constraints = (
        sum(X[(talk, slot)] for talk in range(talks)) <= 1
        for slot in range(slots)
    )
    assert not scheduler.is_valid_solution(X, constraints)


def test_schedule_has_content(solution):
    assert len(solution) > 0


def test_all_events_scheduled(shape, solution):
    scheduled_events = [item[0] for item in solution]
    for event in range(shape.events):
        assert event in scheduled_events


def test_slots_scheduled_once_only(solution):
    for slot, count in Counter(item[1] for item in solution).items():
        assert count <= 1


def test_events_scheduled_once_only(solution):
    for event, count in Counter(item[0] for item in solution).items():
        assert count == 1
