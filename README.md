# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a pet owner plan and track care tasks across multiple pets, using a priority-based scheduler with smart filtering, recurrence, and conflict detection.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, preferences)
- Produce a daily plan and explain why it chose that plan

## Features

| Feature | Description |
|---|---|
| **Multi-pet support** | Add as many pets as you like; each pet owns its own task list |
| **Priority scheduling** | `Scheduler.generate_plan()` sorts tasks by priority (high → low), then by duration, and fits as many as possible within the owner's daily time budget |
| **Sort by time** | `sort_by_time()` orders tasks chronologically by `start_time` (HH:MM); unscheduled tasks appear last |
| **Filter by pet / status** | `filter_tasks()` lets you view one pet's pending tasks or review completed work |
| **Recurring tasks** | Daily and weekly tasks auto-generate their next occurrence when marked complete, using `timedelta` |
| **Conflict detection** | `detect_conflicts()` scans for tasks sharing an exact `start_time`, both within a single pet and across pets; surfaces `st.warning` banners in the UI |
| **Skipped task list** | After generating a plan, tasks that didn't fit the time budget are shown in an expandable panel |
| **Progress bar** | Visual indicator of how much of the day's time budget is consumed by the plan |

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

## Smarter Scheduling

Beyond the core priority-and-time-budget plan, the scheduler includes four algorithmic improvements:

- **Sort by time** — `Scheduler.sort_by_time()` orders all tasks by their `start_time` (HH:MM), placing unscheduled tasks last. Uses `sorted()` with a lambda key so tasks added in any order always display chronologically.
- **Filter by pet / status** — `Scheduler.filter_tasks(pet_name, completed)` returns only the `(pet, task)` pairs matching the given criteria. Useful for showing a single pet's pending tasks or reviewing what has already been done.
- **Recurring tasks** — `Task` carries a `frequency` field (`"daily"`, `"weekly"`, `"as needed"`) and a `due_date`. When `Scheduler.mark_task_complete()` is called on a recurring task, `Task.next_occurrence()` uses Python's `timedelta` to compute the next due date and automatically adds a fresh copy to the pet's task list.
- **Conflict detection** — `Scheduler.detect_conflicts()` scans for tasks that share an exact `start_time`, both within a single pet and across pets (since the owner must be present for both). It returns human-readable warning strings rather than raising exceptions, so the app can surface warnings gracefully.

## Testing PawPal+

Run the full test suite with:

```bash
python -m pytest
```

The suite contains **36 tests** across all four classes, covering:

| Area | What is tested |
|---|---|
| `Task` | `mark_complete()`, `is_high_priority()` threshold, `next_occurrence()` for daily/weekly/as-needed, attribute preservation |
| `Pet` | Task addition and removal (including safe removal of nonexistent names), `get_summary()` |
| `Owner` | Available time, pet addition, cross-pet task aggregation, empty-pets edge case |
| `Scheduler.generate_plan` | Time budget enforcement, priority ordering, skipping completed tasks, empty and over-budget edge cases |
| `Scheduler.sort_by_time` | Chronological ordering, unscheduled tasks sorted last, empty task list |
| `Scheduler.filter_tasks` | Filter by pet name, by completion status (true/false), and no-criteria passthrough |
| `Scheduler.mark_task_complete` + recurrence | Completion flag, daily recurrence adds next occurrence, as-needed does not, unknown pet is safe |
| `Scheduler.detect_conflicts` | No conflict (distinct times), within-pet conflict, cross-pet conflict, unscheduled tasks ignored, completed tasks excluded |

**Confidence level: ★★★★☆**
Core scheduling logic, recurrence, and conflict detection are well covered. The main gap is integration-level testing (e.g., a full session through the Streamlit UI) and validation of edge inputs like negative durations or malformed time strings.

## 📸 Demo

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank"><img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

## Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
