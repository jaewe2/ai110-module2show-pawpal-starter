from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(name="Walk", category="Exercise", duration=20, priority=3,
              frequency="daily", start_time="", due_date="", completed=False):
    return Task(name=name, category=category, duration_minutes=duration,
                priority=priority, frequency=frequency, start_time=start_time,
                due_date=due_date, completed=completed)


def make_owner_with_pet(available_minutes=120):
    pet = Pet(name="Buddy", species="Dog", age=3)
    owner = Owner(name="Alex", available_minutes=available_minutes, pets=[pet])
    return owner, pet


# ---------------------------------------------------------------------------
# Task — happy paths
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    """mark_complete() flips completed from False to True."""
    task = make_task()
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_is_high_priority_true_at_threshold():
    assert make_task(priority=4).is_high_priority() is True
    assert make_task(priority=5).is_high_priority() is True


def test_is_high_priority_false_below_threshold():
    assert make_task(priority=3).is_high_priority() is False
    assert make_task(priority=1).is_high_priority() is False


# ---------------------------------------------------------------------------
# Task — recurrence
# ---------------------------------------------------------------------------

def test_next_occurrence_daily_advances_one_day():
    today = date.today().isoformat()
    task = make_task(frequency="daily", due_date=today)
    nxt = task.next_occurrence()
    expected = (date.today() + timedelta(days=1)).isoformat()
    assert nxt is not None
    assert nxt.due_date == expected
    assert nxt.completed is False


def test_next_occurrence_weekly_advances_seven_days():
    today = date.today().isoformat()
    task = make_task(frequency="weekly", due_date=today)
    nxt = task.next_occurrence()
    expected = (date.today() + timedelta(weeks=1)).isoformat()
    assert nxt is not None
    assert nxt.due_date == expected


def test_next_occurrence_as_needed_returns_none():
    task = make_task(frequency="as needed")
    assert task.next_occurrence() is None


def test_next_occurrence_preserves_task_attributes():
    task = make_task(name="Meds", category="Medical", duration=5, priority=5,
                     frequency="daily", start_time="08:00", due_date="2026-03-25")
    nxt = task.next_occurrence()
    assert nxt.name == "Meds"
    assert nxt.start_time == "08:00"
    assert nxt.priority == 5


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

def test_add_task_increases_count():
    pet = Pet(name="Buddy", species="Dog", age=3)
    assert len(pet.tasks) == 0
    pet.add_task(make_task())
    assert len(pet.tasks) == 1


def test_remove_task_by_name():
    pet = Pet(name="Buddy", species="Dog", age=3)
    pet.add_task(make_task(name="Walk"))
    pet.add_task(make_task(name="Feed"))
    pet.remove_task("Walk")
    assert len(pet.tasks) == 1
    assert pet.tasks[0].name == "Feed"


def test_remove_task_nonexistent_name_is_safe():
    pet = Pet(name="Buddy", species="Dog", age=3)
    pet.add_task(make_task(name="Walk"))
    pet.remove_task("Nonexistent")   # should not raise
    assert len(pet.tasks) == 1


def test_pet_with_no_tasks_get_summary():
    pet = Pet(name="Luna", species="Cat", age=2)
    assert "Luna" in pet.get_summary()
    assert "Cat" in pet.get_summary()


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

def test_owner_get_available_time():
    owner = Owner(name="Alex", available_minutes=60)
    assert owner.get_available_time() == 60


def test_owner_add_pet_increases_count():
    owner = Owner(name="Alex", available_minutes=60)
    assert len(owner.pets) == 0
    owner.add_pet(Pet(name="Buddy", species="Dog", age=3))
    assert len(owner.pets) == 1


def test_owner_get_all_tasks_aggregates_across_pets():
    owner, pet = make_owner_with_pet()
    pet2 = Pet(name="Whiskers", species="Cat", age=5)
    owner.add_pet(pet2)
    pet.add_task(make_task(name="Walk"))
    pet2.add_task(make_task(name="Meds"))
    pairs = owner.get_all_tasks()
    names = [t.name for _, t in pairs]
    assert "Walk" in names
    assert "Meds" in names
    assert len(pairs) == 2


def test_owner_with_no_pets_returns_empty_tasks():
    owner = Owner(name="Alex", available_minutes=60)
    assert owner.get_all_tasks() == []


# ---------------------------------------------------------------------------
# Scheduler — generate_plan
# ---------------------------------------------------------------------------

def test_generate_plan_respects_time_budget():
    owner, pet = make_owner_with_pet(available_minutes=30)
    pet.add_task(make_task(name="Walk",  duration=20, priority=5))
    pet.add_task(make_task(name="Groom", duration=20, priority=3))
    plan = Scheduler(owner).generate_plan()
    total = sum(t.duration_minutes for _, t in plan)
    assert total <= 30


def test_generate_plan_orders_by_priority():
    owner, pet = make_owner_with_pet(available_minutes=120)
    pet.add_task(make_task(name="Low",  duration=10, priority=1))
    pet.add_task(make_task(name="High", duration=10, priority=5))
    plan = Scheduler(owner).generate_plan()
    assert plan[0][1].name == "High"
    assert plan[1][1].name == "Low"


def test_generate_plan_skips_completed_tasks():
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(name="Done", duration=10, priority=5, completed=True))
    pet.add_task(make_task(name="Todo", duration=10, priority=3))
    plan = Scheduler(owner).generate_plan()
    names = [t.name for _, t in plan]
    assert "Done" not in names
    assert "Todo" in names


def test_generate_plan_empty_when_no_tasks():
    owner, pet = make_owner_with_pet()
    assert Scheduler(owner).generate_plan() == []


def test_generate_plan_empty_when_all_tasks_too_long():
    owner, pet = make_owner_with_pet(available_minutes=5)
    pet.add_task(make_task(duration=30, priority=5))
    assert Scheduler(owner).generate_plan() == []


# ---------------------------------------------------------------------------
# Scheduler — sort_by_time
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(name="Afternoon", start_time="15:00"))
    pet.add_task(make_task(name="Morning",   start_time="07:00"))
    pet.add_task(make_task(name="Midday",    start_time="12:00"))
    sorted_pairs = Scheduler(owner).sort_by_time()
    names = [t.name for _, t in sorted_pairs]
    assert names == ["Morning", "Midday", "Afternoon"]


def test_sort_by_time_puts_unscheduled_last():
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(name="NoTime",  start_time=""))
    pet.add_task(make_task(name="HasTime", start_time="09:00"))
    sorted_pairs = Scheduler(owner).sort_by_time()
    assert sorted_pairs[-1][1].name == "NoTime"


def test_sort_by_time_with_no_tasks_returns_empty():
    owner, pet = make_owner_with_pet()
    assert Scheduler(owner).sort_by_time() == []


# ---------------------------------------------------------------------------
# Scheduler — filter_tasks
# ---------------------------------------------------------------------------

def test_filter_by_pet_name():
    owner, pet = make_owner_with_pet()
    pet2 = Pet(name="Whiskers", species="Cat", age=2)
    owner.add_pet(pet2)
    pet.add_task(make_task(name="BuddyTask"))
    pet2.add_task(make_task(name="WhiskersTask"))
    results = Scheduler(owner).filter_tasks(pet_name="Buddy")
    assert all(p.name == "Buddy" for p, _ in results)
    assert len(results) == 1


def test_filter_by_completed_false():
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(name="Done", completed=True))
    pet.add_task(make_task(name="Todo", completed=False))
    results = Scheduler(owner).filter_tasks(completed=False)
    assert len(results) == 1
    assert results[0][1].name == "Todo"


def test_filter_by_completed_true():
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(name="Done", completed=True))
    pet.add_task(make_task(name="Todo", completed=False))
    results = Scheduler(owner).filter_tasks(completed=True)
    assert len(results) == 1
    assert results[0][1].name == "Done"


def test_filter_no_criteria_returns_all():
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(name="A"))
    pet.add_task(make_task(name="B"))
    assert len(Scheduler(owner).filter_tasks()) == 2


# ---------------------------------------------------------------------------
# Scheduler — mark_task_complete + recurrence
# ---------------------------------------------------------------------------

def test_mark_task_complete_sets_flag():
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(name="Walk", frequency="as needed"))
    Scheduler(owner).mark_task_complete("Buddy", "Walk")
    assert pet.tasks[0].completed is True


def test_recurring_daily_task_adds_next_occurrence():
    owner, pet = make_owner_with_pet()
    today = date.today().isoformat()
    pet.add_task(make_task(name="Meds", frequency="daily", due_date=today))
    Scheduler(owner).mark_task_complete("Buddy", "Meds")
    assert len(pet.tasks) == 2
    assert pet.tasks[1].completed is False
    assert pet.tasks[1].due_date == (date.today() + timedelta(days=1)).isoformat()


def test_non_recurring_task_does_not_add_occurrence():
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(name="OneOff", frequency="as needed"))
    Scheduler(owner).mark_task_complete("Buddy", "OneOff")
    assert len(pet.tasks) == 1


def test_mark_complete_unknown_pet_is_safe():
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(name="Walk"))
    Scheduler(owner).mark_task_complete("Ghost", "Walk")  # should not raise
    assert pet.tasks[0].completed is False


# ---------------------------------------------------------------------------
# Scheduler — detect_conflicts
# ---------------------------------------------------------------------------

def test_no_conflicts_when_times_are_distinct():
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(name="Walk", start_time="07:00"))
    pet.add_task(make_task(name="Feed", start_time="08:00"))
    assert Scheduler(owner).detect_conflicts() == []


def test_detects_conflict_within_same_pet():
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(name="Walk", start_time="08:00"))
    pet.add_task(make_task(name="Meds", start_time="08:00"))
    warnings = Scheduler(owner).detect_conflicts()
    assert any("08:00" in w for w in warnings)


def test_detects_cross_pet_conflict():
    owner, pet = make_owner_with_pet()
    pet2 = Pet(name="Whiskers", species="Cat", age=2)
    owner.add_pet(pet2)
    pet.add_task(make_task(name="Walk",     start_time="09:00"))
    pet2.add_task(make_task(name="Feeding", start_time="09:00"))
    warnings = Scheduler(owner).detect_conflicts()
    assert any("09:00" in w for w in warnings)


def test_no_conflict_for_unscheduled_tasks():
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(name="Walk", start_time=""))
    pet.add_task(make_task(name="Feed", start_time=""))
    assert Scheduler(owner).detect_conflicts() == []


def test_completed_tasks_excluded_from_conflict_check():
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(name="OldWalk", start_time="08:00", completed=True))
    pet.add_task(make_task(name="Meds",    start_time="08:00"))
    warnings = Scheduler(owner).detect_conflicts()
    assert warnings == []
