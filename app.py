import os
import re

import streamlit as st

from ai_agent import PawPalAgent
from pawpal_system import Owner, Pet, Scheduler, Task

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Nunito', sans-serif; }

.stApp { background-color: #FFF8F2; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FFF0E6 0%, #FFE4CC 100%);
    border-right: 1px solid #FFD6B0;
}

.hero {
    background: linear-gradient(135deg, #FF6B35 0%, #F4A261 60%, #FFB347 100%);
    border-radius: 24px;
    padding: 36px 48px;
    color: white;
    margin-bottom: 28px;
    box-shadow: 0 10px 40px rgba(255, 107, 53, 0.25);
}
.hero h1 { font-size: 2.8em; font-weight: 800; margin: 0 0 6px; letter-spacing: -1px; }
.hero p  { font-size: 1.1em; margin: 0; opacity: 0.92; }

.card {
    background: white;
    border-radius: 18px;
    padding: 24px 28px;
    box-shadow: 0 2px 16px rgba(0, 0, 0, 0.05);
    border: 1px solid #FFE8D6;
    margin-bottom: 14px;
}
.pet-card-name  { font-size: 1.1em; font-weight: 700; color: #E76F51; }
.pet-card-meta  { color: #888; font-size: 0.88em; margin-top: 2px; }
.pet-card-tasks { font-size: 0.82em; color: #aaa; margin-top: 8px; }

/* Buttons */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #FF6B35, #F4A261) !important;
    color: white !important;
    border: none !important;
    padding: 10px 24px !important;
    transition: all 0.18s ease !important;
    box-shadow: 0 3px 10px rgba(255, 107, 53, 0.2) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(255, 107, 53, 0.35) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: white;
    border-radius: 14px;
    padding: 5px;
    gap: 4px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    border: 1px solid #FFE8D6;
    margin-bottom: 20px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    font-weight: 700 !important;
    color: #aaa !important;
    padding: 10px 28px !important;
    font-size: 1em !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #FF6B35, #F4A261) !important;
    color: white !important;
}

/* Metric tiles */
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #FFE8D6;
    border-radius: 16px;
    padding: 18px 20px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
}
[data-testid="stMetricLabel"]  { font-weight: 700; color: #999; font-size: 0.85em; }
[data-testid="stMetricValue"]  { font-weight: 800; color: #333; }
[data-testid="stMetricDelta"]  { font-weight: 600; }

/* Progress bar */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #FF6B35, #F4A261) !important;
    border-radius: 8px !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    border-radius: 10px !important;
    border-color: #FFD6BA !important;
}
.stSelectbox > div > div { border-radius: 10px !important; }

/* Expanders */
div[data-testid="stExpander"] {
    border: 1px solid #FFE8D6 !important;
    border-radius: 14px !important;
    background: white !important;
}

/* Divider */
hr { border-color: #FFE8D6 !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    api_key_input = st.text_input(
        "Anthropic API Key",
        type="password",
        value=st.session_state.get("api_key", os.environ.get("ANTHROPIC_API_KEY", "")),
        help="Required for AI recommendations and task suggestions.",
    )
    st.session_state["api_key"] = api_key_input

    if api_key_input == "demo":
        st.info("🎭 Demo mode — realistic mock responses")
    elif api_key_input:
        st.success("✓ API key set — AI features active")
    else:
        st.info("Add your API key to unlock AI features. Type **demo** to try mock responses.")

    st.divider()
    st.caption("PawPal+ · Smart pet care, powered by AI")

# ── Session state ─────────────────────────────────────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = None
if "agent" not in st.session_state:
    st.session_state.agent = None


def get_agent() -> PawPalAgent:
    key = st.session_state.get("api_key", "")
    if st.session_state.agent is None or key != st.session_state.get("agent_key"):
        st.session_state.agent = PawPalAgent(api_key=key or None)
        st.session_state["agent_key"] = key
    return st.session_state.agent


# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🐾 PawPal+</h1>
    <p>Your smart pet care scheduler — powered by AI</p>
</div>
""", unsafe_allow_html=True)

# ── Owner profile (collapsible) ───────────────────────────────────────────────
with st.expander("👤 Owner Profile", expanded=st.session_state.owner is None):
    with st.form("owner_form"):
        c1, c2, c3 = st.columns([2, 2, 1])
        owner_name = c1.text_input(
            "Your name",
            value=st.session_state.owner.name if st.session_state.owner else "Jordan",
        )
        available_minutes = c2.number_input(
            "Time available today (min)",
            min_value=10, max_value=480,
            value=st.session_state.owner.available_minutes if st.session_state.owner else 90,
        )
        c3.markdown("<br>", unsafe_allow_html=True)
        submitted = c3.form_submit_button("Save", use_container_width=True)

    if submitted:
        if not owner_name.strip():
            st.error("Owner name cannot be empty.")
        else:
            try:
                existing_pets = st.session_state.owner.pets if st.session_state.owner else []
                st.session_state.owner = Owner(name=owner_name, available_minutes=int(available_minutes))
                st.session_state.owner.pets = existing_pets
                st.success(f"Welcome, {owner_name}! {available_minutes} min budgeted for today.")
            except ValueError as e:
                st.error(str(e))

if st.session_state.owner is None:
    st.info("Fill in your owner profile above to get started.")
    st.stop()

owner: Owner = st.session_state.owner

# ── Metrics row ───────────────────────────────────────────────────────────────
_sched = Scheduler(owner)
_plan  = _sched.generate_plan()
_used  = sum(t.duration_minutes for _, t in _plan)
_confl = _sched.detect_conflicts()
_left  = owner.available_minutes - _used

m1, m2, m3, m4 = st.columns(4)
m1.metric("🐾 Pets", len(owner.pets))
m2.metric("📋 Pending tasks", sum(1 for p in owner.pets for t in p.tasks if not t.completed))
m3.metric("⏱ Time budgeted", f"{_used} min", f"{_left} min left", delta_color="normal")
m4.metric("⚠️ Conflicts", len(_confl), delta_color="inverse" if _confl else "off")

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_pets, tab_schedule, tab_ai = st.tabs(["🐾  My Pets", "📅  Schedule", "🤖  AI Advisor"])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — My Pets
# ═════════════════════════════════════════════════════════════════════════════
with tab_pets:
    col_form, col_list = st.columns([1, 1], gap="large")

    with col_form:
        st.markdown("#### Add a Pet")
        with st.form("pet_form"):
            pet_name = st.text_input("Pet name", value="Mochi")
            r1, r2 = st.columns(2)
            species = r1.selectbox("Species", ["Dog", "Cat", "Other"])
            age     = r2.number_input("Age (years)", min_value=0, max_value=30, value=2)
            special_needs = st.text_input("Special needs (optional)", value="")
            add_pet = st.form_submit_button("Add pet", use_container_width=True)

        if add_pet:
            if not pet_name.strip():
                st.error("Pet name cannot be empty.")
            elif any(p.name == pet_name.strip() for p in owner.pets):
                st.warning(f"A pet named '{pet_name.strip()}' already exists.")
            else:
                try:
                    owner.add_pet(Pet(name=pet_name, species=species, age=int(age), special_needs=special_needs))
                    st.success(f"Added {pet_name.strip()} the {species}!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

    with col_list:
        st.markdown("#### Your Pets")
        if not owner.pets:
            st.info("No pets yet — add one to get started.")
        else:
            for pet in owner.pets:
                icon    = {"Dog": "🐶", "Cat": "🐱"}.get(pet.species, "🐾")
                pending = sum(1 for t in pet.tasks if not t.completed)
                needs   = f" · {pet.special_needs}" if pet.special_needs else ""
                st.markdown(f"""
                <div class="card">
                    <div class="pet-card-name">{icon} {pet.name}</div>
                    <div class="pet-card-meta">{pet.species} &middot; {pet.age} yr{"s" if pet.age != 1 else ""}{needs}</div>
                    <div class="pet-card-tasks">{pending} pending task{"s" if pending != 1 else ""}</div>
                </div>
                """, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — Schedule
# ═════════════════════════════════════════════════════════════════════════════
with tab_schedule:
    if not owner.pets:
        st.warning("Add at least one pet before managing tasks.")
    else:
        col_add, col_view = st.columns([1, 1], gap="large")

        with col_add:
            st.markdown("#### Add a Task")
            with st.form("task_form"):
                target_pet = st.selectbox("Assign to pet", [p.name for p in owner.pets])
                task_name  = st.text_input("Task name", value="Morning walk")
                r1, r2     = st.columns(2)
                category   = r1.selectbox("Category", ["Exercise", "Nutrition", "Medical", "Grooming", "Enrichment", "Other"])
                frequency  = r2.selectbox("Frequency", ["daily", "weekly", "as needed"])
                r3, r4     = st.columns(2)
                duration   = r3.number_input("Duration (min)", min_value=1, max_value=240, value=20)
                priority   = r4.slider("Priority (1–5)", min_value=1, max_value=5, value=3)
                start_time = st.text_input("Start time (HH:MM, optional)", value="")
                add_task   = st.form_submit_button("Add task", use_container_width=True)

            if add_task:
                t_start = start_time.strip()
                if not task_name.strip():
                    st.error("Task name cannot be empty.")
                elif t_start and not _TIME_RE.match(t_start):
                    st.error("Start time must be HH:MM in 24 h format (e.g. 09:30, 14:00).")
                else:
                    try:
                        pet = next(p for p in owner.pets if p.name == target_pet)
                        pet.add_task(Task(
                            name=task_name, category=category,
                            duration_minutes=int(duration), priority=priority,
                            frequency=frequency, start_time=t_start,
                        ))
                        st.success(f"Added '{task_name.strip()}' to {target_pet}.")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

        with col_view:
            st.markdown("#### All Tasks")
            scheduler = Scheduler(owner)
            conflicts = scheduler.detect_conflicts()
            if conflicts:
                st.error("**Schedule conflicts detected** — two tasks share the same start time:")
                for w in conflicts:
                    st.warning(f"⚠ {w}")

            sorted_pairs = scheduler.sort_by_time()
            if sorted_pairs:
                rows = [
                    {
                        "Pet":      pet.name,
                        "Task":     task.name,
                        "Category": task.category,
                        "Start":    task.start_time or "—",
                        "Min":      task.duration_minutes,
                        "Priority": task.priority,
                        "Freq":     task.frequency,
                        "Done":     "✓" if task.completed else "",
                    }
                    for pet, task in sorted_pairs
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No tasks yet — add one on the left.")

        st.divider()

        # ── Generate today's plan ──────────────────────────────────────────
        st.markdown("#### Generate Today's Plan")
        gc1, gc2, gc3 = st.columns([2, 2, 1])
        filter_pet  = gc1.selectbox("Filter by pet", ["All"] + [p.name for p in owner.pets])
        show_filter = gc2.selectbox("Show", ["Pending only", "All tasks"])
        gc3.markdown("<br>", unsafe_allow_html=True)
        gen_btn = gc3.button("Generate", use_container_width=True)

        if gen_btn:
            scheduler = Scheduler(owner)
            conflicts = scheduler.detect_conflicts()
            if conflicts:
                st.error("Fix these conflicts before generating a plan:")
                for w in conflicts:
                    st.warning(f"⚠ {w}")

            fitted_plan = scheduler.generate_plan()
            plan = fitted_plan
            if show_filter == "All tasks":
                plan = list(owner.get_all_tasks())
            if filter_pet != "All":
                plan = [(p, t) for p, t in plan if p.name == filter_pet]

            if not plan:
                st.warning("No tasks could be scheduled — check your time budget or task durations.")
            else:
                total = sum(t.duration_minutes for _, t in plan)
                pct   = min(int(total / owner.get_available_time() * 100), 100)
                st.success(
                    f"Scheduled {len(plan)} task(s) — "
                    f"{total} / {owner.get_available_time()} min ({pct}% of your day)"
                )
                st.progress(pct / 100)

                rows = [
                    {
                        "Pet":           pet.name,
                        "Task":          task.name,
                        "Category":      task.category,
                        "Start":         task.start_time or "—",
                        "Duration (min)": task.duration_minutes,
                        "Priority":      task.priority,
                        "⭐ High Pri":   "⭐" if task.is_high_priority() else "",
                        "Frequency":     task.frequency,
                    }
                    for pet, task in plan
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)

                if show_filter != "All tasks":
                    all_pending = [(p, t) for p, t in owner.get_all_tasks() if not t.completed]
                    skipped = [(p, t) for p, t in all_pending if (p, t) not in fitted_plan]
                    if skipped:
                        with st.expander(f"Tasks that didn't fit today ({len(skipped)})"):
                            for p, t in skipped:
                                st.markdown(
                                    f"- **{p.name}** — {t.name} "
                                    f"({t.duration_minutes} min, priority {t.priority})"
                                )

# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — AI Advisor
# ═════════════════════════════════════════════════════════════════════════════
with tab_ai:
    if not owner.pets:
        st.info("Add at least one pet to use the AI Advisor.")
    else:
        st.markdown(
            "The AI Advisor retrieves relevant pet care knowledge and runs a "
            "**5-step reasoning workflow** to give personalised recommendations."
        )
        st.markdown("<br>", unsafe_allow_html=True)

        selected_pet_name = st.selectbox(
            "Choose a pet to analyse", [p.name for p in owner.pets], key="ai_pet_select"
        )
        selected_pet = next(p for p in owner.pets if p.name == selected_pet_name)

        col_a, col_b = st.columns(2)

        # ── Full agentic analysis ──────────────────────────────────────────
        if col_a.button("🔍 Full AI Analysis", use_container_width=True):
            if not st.session_state.get("api_key"):
                st.warning("Enter your Anthropic API key in the sidebar to use AI features.")
            else:
                with st.spinner("Running 5-step AI reasoning workflow…"):
                    agent  = get_agent()
                    result = agent.analyze_schedule(owner, selected_pet)

                st.success(f"Analysis complete for **{result['pet']}**")

                conf       = result["confidence"]
                conf_color = "green" if conf >= 0.7 else "orange" if conf >= 0.5 else "red"
                st.markdown(
                    f"**Confidence score:** :{conf_color}[{conf:.0%}]  \n"
                    f"*Higher confidence means more relevant knowledge was retrieved and "
                    f"the schedule had fewer issues.*"
                )

                with st.expander("View reasoning steps", expanded=False):
                    for step in result["steps"]:
                        st.markdown(f"**Step {step['step']}: {step['action']}**")
                        if step["step"] == 4:
                            st.markdown(step["result"])
                        else:
                            st.info(step["result"])
                        if "sources" in step:
                            st.caption(f"Sources: {', '.join(step['sources'])}")

                st.markdown("### Recommendations")
                st.markdown(result["recommendations"])

                if result["sources"]:
                    st.caption(f"Knowledge retrieved from: {', '.join(result['sources'])}")

                tr = result["time_remaining"]
                if tr > 0:
                    st.info(f"Time remaining in today's budget: **{tr} min**")
                else:
                    st.warning("No time remaining — consider skipping lower-priority tasks.")

        # ── Quick task suggestions ─────────────────────────────────────────
        if col_b.button("💡 Suggest Tasks", use_container_width=True):
            if not st.session_state.get("api_key"):
                st.warning("Enter your Anthropic API key in the sidebar to use AI features.")
            else:
                with st.spinner("Fetching AI task suggestions…"):
                    agent       = get_agent()
                    suggestions = agent.suggest_tasks(selected_pet, owner)

                tasks = suggestions.get("tasks", [])
                if not tasks:
                    st.warning("No suggestions returned — try again or check your API key.")
                else:
                    st.markdown(f"**Suggested tasks for {selected_pet.name}:**")
                    for td in tasks:
                        sc1, sc2 = st.columns([3, 1])
                        sc1.markdown(
                            f"**{td['name']}** — {td['category']}, "
                            f"{td['duration_minutes']} min, priority {td['priority']}, {td['frequency']}"
                        )
                        if sc2.button("Add", key=f"add_suggested_{td['name']}"):
                            selected_pet.add_task(Task(
                                name=td["name"],
                                category=td["category"],
                                duration_minutes=int(td["duration_minutes"]),
                                priority=int(td["priority"]),
                                frequency=td["frequency"],
                            ))
                            st.success(f"Added '{td['name']}' to {selected_pet.name}!")
                            st.rerun()

                    if suggestions.get("sources"):
                        st.caption(f"Suggestions based on: {', '.join(suggestions['sources'])}")
