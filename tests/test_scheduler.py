import pytest
import numpy as np
from collections import Counter
from conference_scheduler.resources import (
    Event, Slot, ScheduledItem, ChangedEventScheduledItem,
    ChangedSlotScheduledItem
)
from datetime import datetime
from conference_scheduler import scheduler, converter
from conference_scheduler import heuristics as heu
from conference_scheduler.lp_problem import objective_functions as of


# Testing of the three output functions called by external programs

# Solution form
# There is most testing here since the scheduler.solution function is the one
# that sets up the pulp problem and returns the solution from pulp

def test_solution_has_content(solution):
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


def test_total_demand_difference_schedule(slots, events):
    solution = scheduler.solution(
        events=events, slots=slots,
        objective_function=of.efficiency_capacity_demand_difference
    )
    assert type(solution) is list
    assert list(solution) == [(0, 4), (1, 5), (2, 6)]


def test_equity_demand_difference_schedule(slots, events):
    solution = scheduler.solution(
        events=events, slots=slots,
        objective_function=of.equity_capacity_demand_difference
    )
    assert type(solution) is list
    assert list(solution) == [(0, 2), (1, 5), (2, 6)]


def test_small_distance_from_other_schedule(slots, events):
    X_orig = np.array([
        [1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0, 0, 0]
    ])
    schedule = converter.array_to_schedule(array=X_orig, slots=slots,
                                           events=events)
    solution = scheduler.solution(
        events=events, slots=slots,
        objective_function=of.number_of_changes,
        original_schedule=schedule,
    )
    assert type(solution) is list
    assert list(solution) == [(0, 2), (1, 4), (2, 5)]

    X_orig = np.array([
        [0, 0, 0, 0, 0, 0, 1],
        [0, 0, 1, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0, 0]
    ])
    schedule = converter.array_to_schedule(array=X_orig, slots=slots,
                                           events=events)
    solution = scheduler.solution(
        events=events, slots=slots,
        objective_function=of.number_of_changes,
        original_schedule=schedule,
    )
    assert list(solution) == [(0, 2), (1, 4), (2, 5)]


def test_unsolvable_raises_error(events):
    slots = [
        Slot(
            venue='Main Hall', starts_at=datetime(2016, 9, 15, 9, 30),
            duration=30, capacity=50, session="01 Morning A"
        )
    ]
    with pytest.raises(ValueError):
        scheduler.solution(events, slots)


def test_solution_solver_recognised_by_pulp_raises_error(events, slots):
    with pytest.raises(AttributeError):
        scheduler.solution(events, slots, solver="Not a real solver")


def test_array_solver_recognised_by_pulp_raises_error(events, slots):
    with pytest.raises(AttributeError):
        scheduler.array(events, slots, solver="Not a real solver")


def test_schedule_solver_recognised_by_pulp_raises_error(events, slots):
    with pytest.raises(AttributeError):
        scheduler.schedule(events, slots, solver="Not a real solver")

# Array form
# Less testing needed here since it simply calls scheduler.solution and
# converts the result to array form


def test_array_has_content(array):
    assert len(array) > 0


def test_array_shape(array):
    assert array.shape == (3, 7)


def test_array_nonzero(array):
    nonzero = np.transpose(np.nonzero(array))
    assert len(nonzero) == 3


def test_array_contains_ints(array):
    assert all([isinstance(x, np.int8) for x in array.flat])


# Schedule form
# Similar to array form, there is less testsing here since it simply converts
# the output of scheduler.solution to schedule form


def test_schedule_has_content(schedule):
    assert len(schedule) > 0


def test_schedule_has_all_events(schedule, events):
    scheduled_events = [item.event for item in schedule]
    assert scheduled_events == list(events)


# Testing the difference between two schedules

def test_unchanged_event_schedule_difference(events, slots):
    old_schedule = (
        ScheduledItem(events[0], slots[1]),
        ScheduledItem(events[1], slots[4]),
        ScheduledItem(events[2], slots[2])
    )
    difference = scheduler.event_schedule_difference(
        old_schedule, old_schedule)
    assert difference == []


def test_changed_event_schedule_difference(events, slots):
    old_schedule = (
        ScheduledItem(events[0], slots[1]),
        ScheduledItem(events[1], slots[4]),
        ScheduledItem(events[2], slots[2])
    )
    new_schedule = (
        ScheduledItem(events[0], slots[1]),
        ScheduledItem(events[1], slots[3]),
        ScheduledItem(events[2], slots[4])
    )
    difference = scheduler.event_schedule_difference(
        old_schedule, new_schedule)
    expected = [
        ChangedEventScheduledItem(events[1], slots[4], slots[3]),
        ChangedEventScheduledItem(events[2], slots[2], slots[4])
    ]
    assert difference == expected


def test_added_event_schedule_difference(slots):
    events = [
        Event(name='Talk 1', duration=30, demand=30),
        Event(name='Talk 2', duration=30, demand=500),
        Event(name='Workshop 1', duration=60, demand=20),
        Event(name='Workshop 2', duration=60, demand=20)
    ]
    old_schedule = (
        ScheduledItem(events[0], slots[1]),
        ScheduledItem(events[1], slots[4]),
        ScheduledItem(events[2], slots[2])
    )
    new_schedule = (
        ScheduledItem(events[0], slots[1]),
        ScheduledItem(events[1], slots[3]),
        ScheduledItem(events[2], slots[4]),
        ScheduledItem(events[3], slots[5])
    )
    difference = scheduler.event_schedule_difference(
        old_schedule, new_schedule)
    expected = [
        ChangedEventScheduledItem(events[1], slots[4], slots[3]),
        ChangedEventScheduledItem(events[2], slots[2], slots[4]),
        ChangedEventScheduledItem(events[3], None, slots[5])
    ]
    assert difference == expected


def test_removed_event_schedule_difference(slots):
    events = [
        Event(name='Talk 1', duration=30, demand=30),
        Event(name='Talk 2', duration=30, demand=500),
        Event(name='Workshop 1', duration=60, demand=20),
        Event(name='Workshop 2', duration=60, demand=20)
    ]
    old_schedule = (
        ScheduledItem(events[0], slots[1]),
        ScheduledItem(events[1], slots[4]),
        ScheduledItem(events[2], slots[2]),
        ScheduledItem(events[3], slots[5])
    )
    new_schedule = (
        ScheduledItem(events[0], slots[1]),
        ScheduledItem(events[1], slots[3]),
        ScheduledItem(events[2], slots[4])
    )
    difference = scheduler.event_schedule_difference(
        old_schedule, new_schedule)
    expected = [
        ChangedEventScheduledItem(events[1], slots[4], slots[3]),
        ChangedEventScheduledItem(events[2], slots[2], slots[4]),
        ChangedEventScheduledItem(events[3], slots[5], None)
    ]
    assert difference == expected


def test_unchanged_slot_schedule_difference(events, slots):
    old_schedule = (
        ScheduledItem(events[0], slots[1]),
        ScheduledItem(events[1], slots[4]),
        ScheduledItem(events[2], slots[2])
    )
    difference = scheduler.slot_schedule_difference(
        old_schedule, old_schedule)
    assert difference == []


def test_changed_slot_schedule_difference(events, slots):
    old_schedule = (
        ScheduledItem(events[0], slots[1]),
        ScheduledItem(events[1], slots[4]),
        ScheduledItem(events[2], slots[2])
    )
    new_schedule = (
        ScheduledItem(events[0], slots[1]),
        ScheduledItem(events[2], slots[4]),
        ScheduledItem(events[1], slots[2])
    )
    difference = scheduler.slot_schedule_difference(
        old_schedule, new_schedule)
    expected = [
        ChangedSlotScheduledItem(slots[2], events[2], events[1]),
        ChangedSlotScheduledItem(slots[4], events[1], events[2])
    ]
    assert difference == expected


def test_added_slot_schedule_difference(events, slots):
    old_schedule = (
        ScheduledItem(events[0], slots[1]),
        ScheduledItem(events[1], slots[4]),
    )
    new_schedule = (
        ScheduledItem(events[1], slots[1]),
        ScheduledItem(events[0], slots[4]),
        ScheduledItem(events[2], slots[2])
    )
    difference = scheduler.slot_schedule_difference(
        old_schedule, new_schedule)
    expected = [
        ChangedSlotScheduledItem(slots[1], events[0], events[1]),
        ChangedSlotScheduledItem(slots[2], None, events[2]),
        ChangedSlotScheduledItem(slots[4], events[1], events[0])
    ]
    assert difference == expected


def test_removed_slot_schedule_difference(events, slots):
    old_schedule = (
        ScheduledItem(events[0], slots[1]),
        ScheduledItem(events[1], slots[4]),
        ScheduledItem(events[2], slots[2])
    )
    new_schedule = (
        ScheduledItem(events[1], slots[1]),
        ScheduledItem(events[0], slots[4]),
    )
    difference = scheduler.slot_schedule_difference(
        old_schedule, new_schedule)
    expected = [
        ChangedSlotScheduledItem(slots[1], events[0], events[1]),
        ChangedSlotScheduledItem(slots[2], events[2], None),
        ChangedSlotScheduledItem(slots[4], events[1], events[0])
    ]
    assert difference == expected


def test_heuristic_solution(events, slots):
    np.random.seed(1)
    solution = scheduler.heuristic(events=events, slots=slots)

    assert solution == [(0, 4), (1, 0), (2, 6)]


def test_heuristic_solution_with_simulated_annealing(events, slots):
    np.random.seed(1)
    solution = scheduler.heuristic(
        events=events,
        slots=slots,
        algorithm=heu.simulated_annealing,
        objective_function=of.efficiency_capacity_demand_difference)

    assert solution == [(0, 4), (1, 5), (2, 6)]

    solution = scheduler.heuristic(
        events=events,
        slots=slots,
        algorithm=heu.simulated_annealing,
        initial_solution_algorithm_kwargs={"max_iterations": 10},
        objective_function_algorithm_kwargs={"max_iterations": 2},
        objective_function=of.efficiency_capacity_demand_difference)

    assert solution == [(0, 4), (1, 0), (2, 6)]


def test_heuristic_solution_with_sim_annealing_init_sol_and_equity(events,
                                                                   slots):
    np.random.seed(1)
    X_orig = np.array([
        [0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 1]
    ])
    solution = scheduler.heuristic(
        events=events,
        slots=slots,
        algorithm=heu.simulated_annealing,
        initial_solution=X_orig,
        objective_function=of.equity_capacity_demand_difference)

    assert solution == [(0, 3), (1, 4), (2, 6)]

    np.random.seed(1)
    X_orig = np.array([
        [1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 1]
    ])
    solution = scheduler.heuristic(
        events=events,
        slots=slots,
        algorithm=heu.simulated_annealing,
        initial_solution=X_orig,
        objective_function=of.equity_capacity_demand_difference)

    assert solution == [(0, 0), (1, 4), (2, 6)]
