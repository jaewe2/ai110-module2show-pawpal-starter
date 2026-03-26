# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

Beyond the core priority-and-time-budget plan, the scheduler includes four algorithmic improvements:

- **Sort by time** — `Scheduler.sort_by_time()` orders all tasks by their `start_time` (HH:MM), placing unscheduled tasks last. Uses `sorted()` with a lambda key so tasks added in any order always display chronologically.
- **Filter by pet / status** — `Scheduler.filter_tasks(pet_name, completed)` returns only the `(pet, task)` pairs matching the given criteria. Useful for showing a single pet's pending tasks or reviewing what has already been done.
- **Recurring tasks** — `Task` carries a `frequency` field (`"daily"`, `"weekly"`, `"as needed"`) and a `due_date`. When `Scheduler.mark_task_complete()` is called on a recurring task, `Task.next_occurrence()` uses Python's `timedelta` to compute the next due date and automatically adds a fresh copy to the pet's task list.
- **Conflict detection** — `Scheduler.detect_conflicts()` scans for tasks that share an exact `start_time`, both within a single pet and across pets (since the owner must be present for both). It returns human-readable warning strings rather than raising exceptions, so the app can surface warnings gracefully.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
