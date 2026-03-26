# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial UML design centered on four classes with clear, separated responsibilities. `Pet` and `Task` were modeled as simple data-holding objects (later converted to dataclasses), while `Owner` and `Scheduler` carried behavioral logic.

- **Pet** — stores identity and care context for the animal: name, species, age, and any special needs. Responsible for producing a human-readable summary of itself.
- **Task** — represents a single care activity (e.g. walk, feeding, medication) with a duration, category, priority level, and completion status. Responsible for reporting whether it is high priority and for marking itself complete.
- **Owner** — holds the pet owner's name, their `Pet`, and how many minutes per day they have available. Responsible for reporting available time to the scheduler.
- **Scheduler** — the orchestrating class. It holds an `Owner` (and reaches the `Pet` through it) and manages a list of `Task` objects. Responsible for sorting and fitting tasks within the owner's time budget and explaining the resulting plan.

**b. Design changes**

After an AI review of the skeleton, two immediate changes were made:

1. **Removed unused `field` import** — `field` was imported from `dataclasses` but never used in the skeleton. Removing it keeps the imports honest and avoids confusion when implementing methods later.

2. **Converted `Owner` to a `@dataclass`** — the original skeleton used a manual `__init__` for `Owner` while `Pet` and `Task` used `@dataclass`. The AI flagged this as an inconsistency with no justification. Since `Owner` is also a plain data-holding object (name, available_minutes, pet), converting it to a dataclass makes the style uniform across all three value-type classes.

During full implementation, three larger structural changes emerged:

3. **`Pet` now owns tasks** — in the original design, `Scheduler` held the task list. Moving tasks into `Pet` better models reality (a walk belongs to Buddy, not to the scheduler) and made multi-pet support natural.

4. **`Owner` manages multiple pets** — the initial design had one pet per owner. Switching to `list[Pet]` required no logic changes in `Scheduler` because it retrieves tasks through `Owner.get_all_tasks()`.

5. **`Task` gained `start_time`, `due_date`, and `next_occurrence()`** — these were not in the initial UML and were added when implementing sorting, conflict detection, and recurring task features in Phase 3.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers two primary constraints:

- **Time budget** — `Owner.available_minutes` caps the total duration of the day's plan. Tasks are greedily added until no more fit.
- **Priority** — tasks are sorted descending by `priority` (1–5), so high-priority care (medications, feeding) is always scheduled before lower-priority enrichment or grooming.

A secondary sort key (duration ascending) breaks ties between same-priority tasks — shorter tasks are preferred when priority is equal, which maximizes the number of tasks that fit in the available window.

Time and priority were chosen as the primary constraints because they directly reflect real owner constraints: a busy owner has a fixed window and must ensure medical and nutrition tasks happen first. Preferences and pet-specific rules (e.g., "Buddy needs outdoor time before 9am") were consciously deferred as future features to keep the logic layer simple and testable.

**b. Tradeoffs**

The conflict detector checks for **exact start_time matches** rather than overlapping time windows. For example, a 30-minute task starting at 07:00 and a 10-minute task starting at 07:15 would not be flagged — even though they genuinely overlap — because 07:00 ≠ 07:15.

This is a reasonable tradeoff for this scenario because:
1. **Simplicity**: checking exact equality is O(n) per pet with a dictionary; overlap detection would require sorting and comparing intervals (O(n log n)) with more complex logic.
2. **Stage appropriateness**: at this stage of the app, most tasks are short and owners are expected to schedule them intentionally at distinct times. Exact-match detection catches the most obvious mistakes (two tasks assigned the same slot) without over-engineering the constraint layer.
3. **Actionable warnings**: an exact-match conflict always means the schedule is wrong; an overlap might be intentional (e.g., a slow feeding bowl left out during a walk). Exact-match warnings are less likely to produce false positives.

The next iteration could replace this with a proper interval-overlap check using `start_time + duration_minutes` to compute end times.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used across all four phases of this project:

- **Phase 1 (Design)**: AI generated the initial Mermaid.js UML diagram from a plain-English description of the four classes. The most useful prompts were specific: "Review this diagram and flag any missing relationships or unnecessary complexity." This produced concrete, actionable feedback (the missing Owner→Pet ownership relationship, the unused `field` import) rather than generic suggestions.
- **Phase 2 (Skeleton + Implementation)**: AI converted the UML into Python dataclass stubs and later fleshed out method bodies. Prompts like "how should Scheduler retrieve all tasks from Owner's pets?" helped clarify the ownership chain before writing any code.
- **Phase 3 (Algorithms)**: AI suggested using a lambda with a tuple key `(start_time == "", start_time)` to sort tasks while pushing unscheduled ones to the end — a clean Python idiom that would have taken longer to arrive at independently.
- **Phase 4 (Tests)**: AI helped identify edge cases to cover (unknown pet name, as-needed recurrence returning None, completed tasks excluded from conflict checks) that are easy to overlook when writing tests for your own code.

The most effective prompt pattern across all phases was: **give AI the existing file as context, describe what you want, and ask it to flag tradeoffs or problems** rather than just generate code.

**b. Judgment and verification**

During Phase 3, AI initially suggested making `Scheduler` hold a direct reference to a flat `list[Task]` (separate from `Pet`) for simpler sorting and filtering. This was rejected because it would have duplicated data: tasks would exist in both `Pet.tasks` and `Scheduler.tasks`, creating synchronisation bugs whenever a task was added or removed through the `Pet` interface.

The decision was verified by tracing through what `mark_task_complete` and `add_task` would need to do under each design: with the AI's version, both the pet's list and the scheduler's list would need updating on every mutation. With the owner-chain design (`Scheduler → Owner.get_all_tasks() → Pet.tasks`), there is a single source of truth and no duplication. The AI's suggestion optimised for read simplicity at the cost of write correctness — a tradeoff that is wrong for a stateful app.

---

## 4. Testing and Verification

**a. What you tested**

The 36-test suite covers:

- **Task behaviour**: completion, priority threshold, recurrence for all three frequency types, attribute preservation across `next_occurrence()`
- **Pet behaviour**: task addition and removal, safe removal of nonexistent names
- **Owner behaviour**: available time, multi-pet aggregation, empty-pets edge case
- **Scheduler — generate_plan**: time budget enforcement, priority ordering, skipping completed tasks, empty and over-budget edge cases
- **Scheduler — sort_by_time**: chronological order, unscheduled tasks last, empty list
- **Scheduler — filter_tasks**: by pet name, by status, combined, and no-filter passthrough
- **Scheduler — mark_task_complete + recurrence**: flag set, next occurrence added (daily), not added (as needed), unknown pet is a no-op
- **Scheduler — detect_conflicts**: no conflict, within-pet, cross-pet, unscheduled ignored, completed excluded

These tests were important because the scheduling logic depends on several interacting behaviours (sorting, filtering, recurrence) that are easy to break individually without affecting others. Tests isolate each method so regressions are caught immediately.

**b. Confidence**

Confidence level: **★★★★☆**

The core logic is well tested. Remaining gaps:

- **Input validation**: malformed `start_time` (e.g. "9:00" vs "09:00"), negative durations, priority outside 1–5
- **UI integration**: Streamlit session state is not tested; the app's behaviour on repeated reruns is only manually verified
- **Recurrence with no due_date**: `next_occurrence()` falls back to `date.today()` when `due_date` is empty, which may produce surprising results if a task is completed late

---

## 5. Reflection

**a. What went well**

The clearest success was the class ownership structure: `Task` inside `Pet`, `Pet` inside `Owner`, `Scheduler` using `Owner` as a read-only data source. This one design decision made every subsequent feature (sorting, filtering, recurrence, conflict detection) straightforward to implement and test in isolation, because there was always a single authoritative place to read or mutate task data.

**b. What you would improve**

With another iteration, the conflict detector would be upgraded from exact-match to interval-overlap. Storing `start_time` as a string (HH:MM) also creates fragility — a proper `datetime.time` field with validation would make sorting and overlap math significantly cleaner and would eliminate the edge cases around string formatting.

The Streamlit UI would also benefit from a "mark complete" button per task row so the owner can interact with the schedule in real time without editing code.

**c. Key takeaway**

The most important lesson was that **AI is most valuable as a reviewer, not just a generator**. The biggest improvements in this project came not from asking AI to write code from scratch, but from asking it to critique an existing design — "what relationships are missing?", "what edge cases would break this?" — and then deciding which feedback to accept. Staying in the role of lead architect meant treating every AI suggestion as a proposal to evaluate, not an instruction to follow. That discipline kept the design coherent across four phases of incremental development.
