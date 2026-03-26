# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I started with four classes. Pet and Task were basically just data containers — they hold information and don't do much on their own. Owner and Scheduler were where the real logic lived.

- **Pet** — stores the animal's name, species, age, and any special needs. It can also give you a quick readable summary of itself.
- **Task** — represents one care activity like a walk or medication. It knows its duration, priority, and whether it's been done.
- **Owner** — holds the owner's name and how many minutes they have available in the day.
- **Scheduler** — the brain of the app. It takes the owner's info and figures out which tasks to do today based on time and priority.

**b. Design changes**

A couple small things changed after an AI review of the early skeleton:

1. I removed an unused `field` import — it got added automatically but was never actually used.
2. I made `Owner` a dataclass to match how `Pet` and `Task` were already set up. It was inconsistent before with no good reason.

Bigger changes came during building:

3. I moved tasks into `Pet` instead of `Scheduler`. It just made more sense — Buddy's walk belongs to Buddy, not to the scheduler.
4. I changed `Owner` to hold a list of pets instead of just one. This made multi-pet support easy.
5. I added `start_time`, `due_date`, and a `next_occurrence()` method to `Task` once I started building the sorting and recurring task features.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler looks at two things: how much time the owner has and how important each task is.

Tasks are sorted by priority first (5 is most important, 1 is least). If two tasks have the same priority, shorter ones go first so you can fit more into the day. It keeps adding tasks until there's no more time left.

I focused on time and priority because those are the most real constraints a pet owner actually has. Things like "Buddy needs a walk before 9am" could be added later — I didn't want to over-build it before the basics worked.

**b. Tradeoffs**

The conflict checker only catches tasks that have the exact same start time. So if one task starts at 07:00 and another starts at 07:15, it won't flag that — even if they technically overlap.

I kept it simple like this because:
- It catches the most obvious mistake (two things literally scheduled at the same time)
- It's less likely to give false alarms — sometimes overlaps are fine, like leaving a food bowl out during a walk
- Adding real interval overlap detection would've been a lot more code for a feature that probably won't matter much at this stage

If I kept building this, I'd switch to checking actual start and end times.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI throughout the whole project but in different ways at each phase.

In the design phase, I asked it to generate a UML diagram and then reviewed what it made. Asking it to "flag missing relationships or unnecessary complexity" was way more useful than just asking it to "make a diagram."

When building the skeleton, I asked things like "how should Scheduler get tasks from the Owner's pets?" which helped me figure out the right structure before I wrote any real code.

For the algorithm work, AI suggested using a tuple key `(start_time == "", start_time)` for sorting — a neat Python trick for pushing empty values to the end. That would've taken me a while to figure out on my own.

For tests, it helped me think of edge cases I would've missed, like what happens if you try to mark a task complete for a pet that doesn't exist.

**b. Judgment and verification**

At one point AI suggested having Scheduler hold its own flat list of tasks, separate from Pet. I didn't go with that because it would have meant storing the same task in two places — once in the pet and once in the scheduler. Any time you added or removed a task, you'd have to update both lists, which would cause bugs.

I thought it through by asking: what would `add_task` and `mark_task_complete` have to do under each design? With the AI's version, both places need updating every time. With the approach I used, there's only one place tasks live (inside Pet), and the Scheduler just reads them through the owner. Simpler and less error-prone.

---

## 4. Testing and Verification

**a. What you tested**

I wrote 36 tests total. Here's what they cover:

- Task: marking complete, checking priority level, generating the next occurrence for daily/weekly/as-needed tasks
- Pet: adding and removing tasks, including safely removing a task that doesn't exist
- Owner: getting available time, adding pets, pulling all tasks across multiple pets
- Scheduler generate_plan: stays within the time budget, orders by priority, skips completed tasks, handles an empty task list
- Scheduler sort_by_time: comes back in order, unscheduled tasks go last
- Scheduler filter_tasks: by pet name, by completion status, or no filter at all
- Scheduler mark_task_complete: sets the flag, adds next occurrence for recurring tasks, does nothing if the pet doesn't exist
- Scheduler detect_conflicts: catches same-time conflicts within one pet and across pets, ignores unscheduled or completed tasks

These were important because a lot of features depend on each other. If recurrence breaks, it could mess up the plan. Tests let me catch problems in one place without having to run the whole app.

**b. Confidence**

Confidence: **★★★★☆**

The core logic works and is tested well. A few things I'd still want to cover:

- What happens with a badly formatted start_time like "9:00" instead of "09:00"
- The Streamlit UI isn't tested — I only checked it manually
- If a task has no due_date and you mark it complete, it falls back to today's date, which could be off

---

## 5. Reflection

**a. What went well**

The part I'm most happy with is how the classes relate to each other. Task lives inside Pet, Pet lives inside Owner, and Scheduler just asks Owner for what it needs. Once that structure was right, everything else — sorting, filtering, recurring tasks, conflict detection — was pretty straightforward to add. I never had to dig through a messy global list or worry about duplicate data.

**b. What you would improve**

I'd improve the conflict detection first. Right now it only catches exact time matches. Real overlap detection (e.g., a 30-min task at 7:00 blocking anything before 7:30) would be more useful in practice.

I'd also change `start_time` from a plain string to an actual `datetime.time` object. Right now it's easy to enter "9:00" instead of "09:00" and things get weird. Using a real time type would fix that and make the math cleaner.

And I'd add a "mark complete" button in the Streamlit UI so owners can check off tasks without touching any code.

**c. Key takeaway**

The biggest thing I learned is that AI works best when you treat it like a collaborator you're reviewing, not a source of final answers. The most useful moments weren't "write me a scheduler" — they were "here's what I built, what's wrong with it?" That's when AI actually caught real problems and helped improve the design. Staying in charge of the decisions made the project feel more coherent and easier to explain.
