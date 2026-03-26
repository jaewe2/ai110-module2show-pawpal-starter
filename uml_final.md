# PawPal+ — Final Class Diagram

```mermaid
classDiagram
    class Task {
        +str name
        +str category
        +int duration_minutes
        +int priority
        +str frequency
        +bool completed
        +str start_time
        +str due_date
        +mark_complete()
        +is_high_priority() bool
        +next_occurrence() Task
    }

    class Pet {
        +str name
        +str species
        +int age
        +str special_needs
        +list~Task~ tasks
        +get_summary() str
        +add_task(task)
        +remove_task(name)
    }

    class Owner {
        +str name
        +int available_minutes
        +list~Pet~ pets
        +add_pet(pet)
        +get_available_time() int
        +get_all_tasks() list
    }

    class Scheduler {
        +Owner owner
        +generate_plan() list
        +sort_by_time() list
        +filter_tasks(pet_name, completed) list
        +mark_task_complete(pet_name, task_name)
        +detect_conflicts() list
        +explain_plan() str
    }

    Pet "1" *-- "*" Task : owns
    Owner "1" *-- "*" Pet : manages
    Scheduler --> Owner : uses
```

## Key changes from initial design

| Change | Reason |
|---|---|
| `Task` gained `start_time`, `due_date`, `frequency`, `next_occurrence()` | Needed for sorting, recurrence, and conflict detection |
| `Pet` now owns a `list[Task]` | Tasks belong to a specific pet, not a global list |
| `Owner` now manages `list[Pet]` | Multi-pet support required for realistic scheduling |
| `Scheduler` gained `sort_by_time()`, `filter_tasks()`, `detect_conflicts()` | Phase 3 algorithm features |
| `Scheduler` no longer holds `tasks` directly | Tasks are owned by `Pet`; Scheduler retrieves them via `Owner.get_all_tasks()` |
