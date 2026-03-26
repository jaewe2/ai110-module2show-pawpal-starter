from pawpal_system import Owner, Pet, Task, Scheduler

# ---------------------------------------------------------------------------
# Setup — tasks added OUT OF ORDER on purpose to test sort_by_time()
# ---------------------------------------------------------------------------
buddy = Pet(name="Buddy", species="Dog", age=3)
whiskers = Pet(name="Whiskers", species="Cat", age=5, special_needs="Thyroid medication twice daily")

buddy.add_task(Task(name="Fetch / Playtime", category="Enrichment",  duration_minutes=20, priority=3, frequency="daily",    start_time="15:00"))
buddy.add_task(Task(name="Morning Walk",     category="Exercise",    duration_minutes=30, priority=5, frequency="daily",    start_time="07:00"))
buddy.add_task(Task(name="Feeding",          category="Nutrition",   duration_minutes=10, priority=5, frequency="daily",    start_time="08:00"))
buddy.add_task(Task(name="Nail Trim",        category="Grooming",    duration_minutes=15, priority=2, frequency="weekly",   start_time=""))     # unscheduled

whiskers.add_task(Task(name="Thyroid Medication", category="Medical",  duration_minutes=5,  priority=5, frequency="daily",  start_time="08:00", due_date="2026-03-25"))
whiskers.add_task(Task(name="Brush Coat",         category="Grooming", duration_minutes=15, priority=2, frequency="weekly", start_time="16:00"))
# Intentional conflict — same time as Buddy's Feeding
whiskers.add_task(Task(name="Lunchtime Feeding",  category="Nutrition", duration_minutes=10, priority=4, frequency="daily", start_time="08:00"))

owner = Owner(name="Alex", available_minutes=90)
owner.add_pet(buddy)
owner.add_pet(whiskers)

scheduler = Scheduler(owner)

# ---------------------------------------------------------------------------
# 1. Today's schedule (priority-sorted, time-fitted)
# ---------------------------------------------------------------------------
plan = scheduler.generate_plan()

print("=" * 50)
print("         TODAY'S SCHEDULE")
print(f"         Owner: {owner.name}  |  Budget: {owner.get_available_time()} min")
print("=" * 50)
total = 0
for pet, task in plan:
    flag = " (!)" if task.is_high_priority() else ""
    print(f"  {pet.name:<10} | {task.name:<22} | {task.duration_minutes:>3} min | p{task.priority}{flag}")
    total += task.duration_minutes
print("-" * 50)
print(f"  {'TOTAL':<10}   {'':22}   {total:>3} min used")
print("=" * 50)

# ---------------------------------------------------------------------------
# 2. Sorted by start_time
# ---------------------------------------------------------------------------
print("\n--- ALL TASKS SORTED BY START TIME ---")
for pet, task in scheduler.sort_by_time():
    time_label = task.start_time if task.start_time else "(unscheduled)"
    print(f"  {time_label}  [{pet.name}] {task.name}")

# ---------------------------------------------------------------------------
# 3. Filtering — incomplete tasks for Buddy only
# ---------------------------------------------------------------------------
print("\n--- BUDDY'S INCOMPLETE TASKS ---")
for pet, task in scheduler.filter_tasks(pet_name="Buddy", completed=False):
    print(f"  {task.name} ({task.category})")

# ---------------------------------------------------------------------------
# 4. Recurring task — mark Whiskers' medication complete, check next occurrence
# ---------------------------------------------------------------------------
print("\n--- RECURRING TASK TEST ---")
print(f"  Whiskers tasks before: {len(whiskers.tasks)}")
scheduler.mark_task_complete("Whiskers", "Thyroid Medication")
print(f"  Whiskers tasks after:  {len(whiskers.tasks)}  (next occurrence auto-added)")
next_med = whiskers.tasks[-1]
print(f"  New task due: {next_med.due_date}  |  completed: {next_med.completed}")

# ---------------------------------------------------------------------------
# 5. Conflict detection
# ---------------------------------------------------------------------------
print("\n--- CONFLICT DETECTION ---")
conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        print(f"  WARNING: {warning}")
else:
    print("  No conflicts found.")
print()
