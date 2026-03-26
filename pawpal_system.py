from dataclasses import dataclass, field


@dataclass
class Task:
    name: str
    category: str
    duration_minutes: int
    priority: int                  # 1 (low) to 5 (high)
    frequency: str = "daily"       # e.g. "daily", "weekly", "as needed"
    completed: bool = False

    def mark_complete(self):
        """Mark this task as completed."""
        self.completed = True

    def is_high_priority(self) -> bool:
        """Return True if the task's priority is 4 or higher."""
        return self.priority >= 4


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

    def mark_task_complete(self, pet_name: str, task_name: str):
        """Mark a specific pet's task as complete."""
        for pet in self.owner.pets:
            if pet.name == pet_name:
                for task in pet.tasks:
                    if task.name == task_name:
                        task.mark_complete()
                        return
