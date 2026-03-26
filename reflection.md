# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial UML design centered on four classes with clear, separated responsibilities. `Pet` and `Task` were modeled as simple data-holding objects (later converted to dataclasses), while `Owner` and `Scheduler` carried behavioral logic.

- **Pet** — stores identity and care context for the animal: name, species, age, and any special needs. Responsible for producing a human-readable summary of itself.
- **Task** — represents a single care activity (e.g. walk, feeding, medication) with a duration, category, priority level, and completion status. Responsible for reporting whether it is high priority and for marking itself complete.
- **Owner** — holds the pet owner's name, their `Pet`, and how many minutes per day they have available. Responsible for reporting available time to the scheduler.
- **Scheduler** — the orchestrating class. It holds an `Owner` (and reaches the `Pet` through it) and manages a list of `Task` objects. Responsible for sorting and fitting tasks within the owner's time budget and explaining the resulting plan.

**b. Design changes**

After an AI review of the skeleton, two changes were made:

1. **Removed unused `field` import** — `field` was imported from `dataclasses` but never used in the skeleton. Removing it keeps the imports honest and avoids confusion when implementing methods later.

2. **Converted `Owner` to a `@dataclass`** — the original skeleton used a manual `__init__` for `Owner` while `Pet` and `Task` used `@dataclass`. The AI flagged this as an inconsistency with no justification. Since `Owner` is also a plain data-holding object (name, available_minutes, pet), converting it to a dataclass makes the style uniform across all three value-type classes.

Changes **not** made (deferred to implementation):
- Priority range validation on `Task` — will add when implementing `is_high_priority()`.
- Tie-breaking in `generate_plan()` — will define a consistent rule when implementing scheduling logic.
- `get_available_time()` passthrough — kept for now in case time tracking becomes dynamic; will remove if it stays trivial after implementation.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
