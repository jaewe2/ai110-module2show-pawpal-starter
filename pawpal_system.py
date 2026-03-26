from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


@dataclass
class Task:
    name: str
    category: str
    duration_minutes: int
    priority: int                  # 1 (low) to 5 (high)
    frequency: str = "daily"       # "daily", "weekly", "as needed"
    completed: bool = False
    start_time: str = ""           # "HH:MM" — empty means unscheduled
    due_date: str = ""             # "YYYY-MM-DD" — empty means no due date

    def mark_complete(self):
        """Mark this task as completed."""
        self.completed = True

    def is_high_priority(self) -> bool:
        """Return True if the task's priority is 4 or higher."""
        return self.priority >= 4

    def next_occurrence(self) -> "Task | None":
        """Return a new incomplete Task due on the next occurrence, or None for 'as needed'."""
        if self.frequency == "as needed":
            return None
        base = date.fromisoformat(self.due_date) if self.due_date else date.today()
        delta = timedelta(days=1) if self.frequency == "daily" else timedelta(weeks=1)
        return Task(
            name=self.name,
            category=self.category,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            start_time=self.start_time,
            due_date=(base + delta).isoformat(),
        )


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: str = ""
    tasks: list[Task] = field(default_factory=list)

    def get_summary(self) -> str:
        """Return a human-readable description of the pet."""
        summary = f"{self.name} ({self.species}, age {self.age})"
        if self.special_needs:
            summary += f" — special needs: {self.special_needs}"
        return summary

    def add_task(self, task: Task):
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, name: str):
        """Remove all tasks matching the given name from this pet's task list."""
        self.tasks = [t for t in self.tasks if t.name != name]


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet):
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def get_available_time(self) -> int:
        """Return the owner's total available minutes for the day."""
        return self.available_minutes

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all (pet, task) pairs across every pet."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    def generate_plan(self) -> list[tuple[Pet, Task]]:
        """Return a time-fitted list of (pet, task) pairs sorted by priority then duration."""
        all_pairs = self.owner.get_all_tasks()
        pending = [(pet, t) for pet, t in all_pairs if not t.completed]
        sorted_pairs = sorted(pending, key=lambda x: (-x[1].priority, x[1].duration_minutes))

        plan: list[tuple[Pet, Task]] = []
        time_remaining = self.owner.get_available_time()
        for pet, task in sorted_pairs:
            if task.duration_minutes <= time_remaining:
                plan.append((pet, task))
                time_remaining -= task.duration_minutes
        return plan

    def sort_by_time(self) -> list[tuple[Pet, Task]]:
        """Return all tasks sorted by start_time (HH:MM); unscheduled tasks appear last."""
        all_pairs = self.owner.get_all_tasks()
        return sorted(all_pairs, key=lambda x: (x[1].start_time == "", x[1].start_time))

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[tuple[Pet, Task]]:
        """Filter (pet, task) pairs by pet name and/or completion status."""
        pairs = self.owner.get_all_tasks()
        if pet_name is not None:
            pairs = [(p, t) for p, t in pairs if p.name == pet_name]
        if completed is not None:
            pairs = [(p, t) for p, t in pairs if t.completed == completed]
        return pairs

    def mark_task_complete(self, pet_name: str, task_name: str):
        """Mark a task complete and queue the next occurrence for recurring tasks."""
        for pet in self.owner.pets:
            if pet.name == pet_name:
                for task in pet.tasks:
                    if task.name == task_name and not task.completed:
                        task.mark_complete()
                        next_task = task.next_occurrence()
                        if next_task:
                            pet.add_task(next_task)
                        return

    def detect_conflicts(self) -> list[str]:
        """Return warning strings for any tasks that share an exact start_time."""
        warnings: list[str] = []

        # Within each pet
        for pet in self.owner.pets:
            seen: dict[str, str] = {}
            for task in pet.tasks:
                if not task.start_time or task.completed:
                    continue
                if task.start_time in seen:
                    warnings.append(
                        f"Conflict [{pet.name}]: '{seen[task.start_time]}' and "
                        f"'{task.name}' both start at {task.start_time}"
                    )
                else:
                    seen[task.start_time] = task.name

        # Across pets (owner must be present for both)
        cross: dict[str, list[str]] = {}
        for pet in self.owner.pets:
            for task in pet.tasks:
                if not task.start_time or task.completed:
                    continue
                cross.setdefault(task.start_time, []).append(f"{pet.name}/{task.name}")
        for time_slot, entries in cross.items():
            if len(entries) > 1:
                warnings.append(
                    f"Cross-pet conflict at {time_slot}: {', '.join(entries)}"
                )

        return warnings

    def explain_plan(self) -> str:
        """Return a formatted string summarizing today's scheduled tasks and total time used."""
        plan = self.generate_plan()
        if not plan:
            return "No tasks could be scheduled within the available time."
        lines = [f"Daily plan for {self.owner.name}'s pets:"]
        total = 0
        for pet, task in plan:
            flag = " [!]" if task.is_high_priority() else ""
            lines.append(
                f"  [{pet.name}] {task.name} — {task.category}, "
                f"{task.duration_minutes} min, priority {task.priority}{flag}"
            )
            total += task.duration_minutes
        lines.append(f"Total: {total} / {self.owner.get_available_time()} min")
        return "\n".join(lines)
