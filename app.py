import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Your smart pet care scheduler")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

# ---------------------------------------------------------------------------
# Section 1: Owner setup
# ---------------------------------------------------------------------------
st.subheader("Owner Info")

with st.form("owner_form"):
    owner_name = st.text_input("Your name", value="Jordan")
    available_minutes = st.number_input(
        "Time available today (minutes)", min_value=10, max_value=480, value=90
    )
    submitted = st.form_submit_button("Save owner")

if submitted:
    existing_pets = st.session_state.owner.pets if st.session_state.owner else []
    st.session_state.owner = Owner(name=owner_name, available_minutes=int(available_minutes))
    st.session_state.owner.pets = existing_pets
    st.success(f"Saved: {owner_name} with {available_minutes} min available today.")

if st.session_state.owner is None:
    st.info("Fill in your owner info above to get started.")
    st.stop()

owner: Owner = st.session_state.owner

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Add a pet
# ---------------------------------------------------------------------------
st.subheader("Add a Pet")

with st.form("pet_form"):
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
    special_needs = st.text_input("Special needs (optional)", value="")
    add_pet = st.form_submit_button("Add pet")

if add_pet:
    owner.add_pet(Pet(name=pet_name, species=species, age=int(age), special_needs=special_needs))
    st.success(f"Added {pet_name} the {species}!")

if owner.pets:
    for pet in owner.pets:
        st.markdown(f"- {pet.get_summary()}")
else:
    st.info("No pets yet — add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Add a task
# ---------------------------------------------------------------------------
st.subheader("Add a Task")

if not owner.pets:
    st.warning("Add at least one pet before adding tasks.")
else:
    with st.form("task_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            target_pet = st.selectbox("Assign to pet", [p.name for p in owner.pets])
            task_name  = st.text_input("Task name", value="Morning walk")
            category   = st.selectbox("Category", ["Exercise", "Nutrition", "Medical", "Grooming", "Enrichment", "Other"])
        with col_b:
            duration   = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
            priority   = st.slider("Priority (1=low, 5=high)", min_value=1, max_value=5, value=3)
            frequency  = st.selectbox("Frequency", ["daily", "weekly", "as needed"])
            start_time = st.text_input("Start time (HH:MM, optional)", value="")
        add_task = st.form_submit_button("Add task")

    if add_task:
        pet = next(p for p in owner.pets if p.name == target_pet)
        pet.add_task(Task(
            name=task_name,
            category=category,
            duration_minutes=int(duration),
            priority=priority,
            frequency=frequency,
            start_time=start_time.strip(),
        ))
        st.success(f"Added '{task_name}' to {target_pet}.")

    # --- Conflict warnings ---
    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.error("**Schedule conflicts detected** — two tasks share the same start time:")
        for w in conflicts:
            st.warning(f"⚠ {w}")

    # --- Task list sorted by time ---
    sorted_pairs = scheduler.sort_by_time()
    if sorted_pairs:
        st.markdown("**All tasks (sorted by start time):**")
        rows = []
        for pet, task in sorted_pairs:
            rows.append({
                "Pet": pet.name,
                "Task": task.name,
                "Category": task.category,
                "Start": task.start_time or "—",
                "Duration (min)": task.duration_minutes,
                "Priority": task.priority,
                "Frequency": task.frequency,
                "Done": "Yes" if task.completed else "No",
            })
        st.table(rows)
    else:
        st.info("No tasks yet — add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 4: Generate schedule
# ---------------------------------------------------------------------------
st.subheader("Generate Today's Schedule")

col1, col2 = st.columns(2)
filter_pet  = col1.selectbox("Filter by pet (optional)", ["All"] + [p.name for p in owner.pets])
show_filter = col2.selectbox("Show", ["Pending only", "All tasks"])

if st.button("Generate schedule"):
    scheduler = Scheduler(owner)

    # Conflict check before showing plan
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.error("Fix these conflicts before generating a plan:")
        for w in conflicts:
            st.warning(f"⚠ {w}")

    plan = scheduler.generate_plan()

    # Apply pet filter
    if filter_pet != "All":
        plan = [(p, t) for p, t in plan if p.name == filter_pet]

    if not plan:
        st.warning("No tasks could be scheduled — check your time budget or task durations.")
    else:
        total = sum(t.duration_minutes for _, t in plan)
        pct   = int(total / owner.get_available_time() * 100)

        st.success(f"Scheduled {len(plan)} task(s) — {total} / {owner.get_available_time()} min ({pct}% of your day)")
        st.progress(pct / 100)

        rows = []
        for pet, task in plan:
            rows.append({
                "Pet":           pet.name,
                "Task":          task.name,
                "Category":      task.category,
                "Start":         task.start_time or "—",
                "Duration (min)": task.duration_minutes,
                "Priority":      task.priority,
                "High priority": "Yes" if task.is_high_priority() else "No",
                "Frequency":     task.frequency,
            })
        st.table(rows)

        # Pending tasks that didn't fit
        all_pending = [(p, t) for p, t in owner.get_all_tasks() if not t.completed]
        skipped = [(p, t) for p, t in all_pending if (p, t) not in plan]
        if skipped:
            with st.expander(f"Tasks that didn't fit today ({len(skipped)})"):
                for p, t in skipped:
                    st.markdown(f"- **{p.name}** — {t.name} ({t.duration_minutes} min, priority {t.priority})")
