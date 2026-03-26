from dataclasses import dataclass, field


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: str = ""

    def get_summary(self) -> str:
        pass


@dataclass
class Task:
    name: str
    category: str
    duration_minutes: int
    priority: int
    completed: bool = False

    def mark_complete(self):
        pass

    def is_high_priority(self) -> bool:
        pass


class Owner:
    def __init__(self, name: str, available_minutes: int, pet: Pet):
        self.name = name
        self.available_minutes = available_minutes
        self.pet = pet

    def get_available_time(self) -> int:
        pass


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner
        self.tasks: list[Task] = []

    def add_task(self, task: Task):
        pass

    def remove_task(self, name: str):
        pass

    def generate_plan(self) -> list[Task]:
        pass

    def explain_plan(self) -> str:
        pass
