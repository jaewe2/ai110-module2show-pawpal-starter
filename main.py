from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
buddy = Pet(name="Buddy", species="Dog", age=3)
whiskers = Pet(name="Whiskers", species="Cat", age=5, special_needs="Thyroid medication twice daily")

buddy.add_task(Task(name="Morning Walk", category="Exercise", duration_minutes=30, priority=5, frequency="daily"))
buddy.add_task(Task(name="Feeding", category="Nutrition", duration_minutes=10, priority=5, frequency="daily"))
buddy.add_task(Task(name="Fetch / Playtime", category="Enrichment", duration_minutes=20, priority=3, frequency="daily"))

whiskers.add_task(Task(name="Thyroid Medication", category="Medical", duration_minutes=5, priority=5, frequency="daily"))
whiskers.add_task(Task(name="Brush Coat", category="Grooming", duration_minutes=15, priority=2, frequency="weekly"))

owner = Owner(name="Alex", available_minutes=90)
owner.add_pet(buddy)
owner.add_pet(whiskers)

# --- Schedule ---
scheduler = Scheduler(owner)
plan = scheduler.generate_plan()

print("=" * 40)
print("       TODAY'S SCHEDULE")
print(f"       Owner: {owner.name}")
print(f"       Time budget: {owner.get_available_time()} min")
print("=" * 40)

if not plan:
    print("No tasks could fit in today's schedule.")
else:
    total = 0
    for pet, task in plan:
        priority_flag = " (!)" if task.is_high_priority() else ""
        print(f"  {pet.name:<10} | {task.name:<22} | {task.duration_minutes:>3} min | priority {task.priority}{priority_flag}")
        total += task.duration_minutes
    print("-" * 40)
    print(f"  {'TOTAL':<10}   {'':22}   {total:>3} min used")

print("=" * 40)
