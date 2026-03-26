from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    task = Task(name="Morning Walk", category="Exercise", duration_minutes=30, priority=5)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", species="Dog", age=3)
    assert len(pet.tasks) == 0
    pet.add_task(Task(name="Feeding", category="Nutrition", duration_minutes=10, priority=5))
    assert len(pet.tasks) == 1
