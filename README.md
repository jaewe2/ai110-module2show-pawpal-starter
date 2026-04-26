# PawPal+ Final — Applied AI Pet Care System

> **Base project:** PawPal+ (Module 2) — a priority-based pet care scheduler that lets owners add pets, create tasks with priorities and recurrence, detect scheduling conflicts, and generate a daily plan that fits within their available time. The Module 2 system was fully rule-based: no AI, no external APIs, just Python logic and a Streamlit UI.

> **This extension** transforms PawPal+ into an end-to-end applied AI system by adding a RAG-powered knowledge base, a 5-step agentic reasoning workflow, live Claude API integration, confidence scoring, structured logging, and a comprehensive evaluation suite.

---

## Demo Walkthrough

> 📹 **Loom video:** [Watch the full demo walkthrough](https://www.loom.com/share/728fec3a2da341e791575b2b9630be14)

---

## What This System Does

PawPal+ Final helps pet owners manage their pets' daily care schedules and get personalised, AI-generated recommendations based on each pet's species, age, and special needs.

**Core features (from Module 2):**
- Add owners, pets, and care tasks with priority, duration, frequency, and start time
- Generate a priority-sorted daily schedule that fits within the owner's time budget
- Detect scheduling conflicts (tasks sharing the same start time, within and across pets)
- Recurring tasks — daily and weekly tasks auto-create their next occurrence when completed

**New AI features:**
- **RAG (Retrieval-Augmented Generation):** A local knowledge base of pet care documents is searched before every AI call. Only relevant passages are passed to Claude, grounding responses in factual care guidance rather than general model knowledge.
- **Agentic Workflow:** A 5-step reasoning pipeline (profile → retrieve → evaluate → recommend → validate) with visible intermediate steps so users can audit the AI's reasoning.
- **Task suggestions:** One-click AI task generation based on the pet's species and age, with user confirmation before any task is added.
- **Confidence scoring:** Each analysis returns a calibrated 0–1 score based on retrieval relevance, schedule conflicts, and special-needs flags.
- **Structured logging:** All API calls, retrieval results, and errors are written to `logs/pawpal_agent.log`.
- **Human-in-the-loop design:** No task is ever added automatically — every AI suggestion requires a manual click to confirm.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Streamlit UI (app.py)                │
│  Owner/Pet/Task input ──► Schedule view ──► AI Advisor   │
└───────────────┬──────────────────────────┬──────────────┘
                │                          │
     ┌──────────▼─────────┐    ┌───────────▼──────────────┐
     │  pawpal_system.py  │    │       ai_agent.py         │
     │  Owner / Pet /     │    │  ┌─────────────────────┐  │
     │  Task / Scheduler  │    │  │   KnowledgeBase      │  │
     └────────────────────┘    │  │  (RAG retriever)     │  │
                               │  └──────────┬──────────┘  │
                               │             │              │
                               │  ┌──────────▼──────────┐  │
                               │  │   PawPalAgent        │  │
                               │  │  5-step workflow:    │  │
                               │  │  1. Profile          │  │
                               │  │  2. RAG retrieve     │  │
                               │  │  3. Schedule eval    │  │
                               │  │  4. Claude API       │  │
                               │  │  5. Budget validate  │  │
                               │  └──────────┬──────────┘  │
                               └─────────────┼─────────────┘
                                             │
                               ┌─────────────▼─────────────┐
                               │    Anthropic Claude API    │
                               │    (claude-opus-4-7)       │
                               └───────────────────────────┘
                                             │
                         ┌───────────────────┤
                         │                   │
              ┌──────────▼───────┐  ┌────────▼────────┐
              │  logs/           │  │  evaluator.py   │
              │  pawpal_agent.log│  │  (test harness) │
              │  evaluation_     │  └─────────────────┘
              │  results.json    │
              └──────────────────┘
```

**Data flow:**
1. User fills in owner/pet/task info in the Streamlit UI.
2. `pawpal_system.py` handles all scheduling logic (conflict detection, plan generation, recurrence).
3. When the user clicks "Analyse Schedule," `PawPalAgent` runs the 5-step workflow: builds a pet context string, queries `KnowledgeBase` with keyword matching, evaluates the current schedule, calls the Claude API with retrieved context + pet profile, and checks remaining time budget.
4. Results (recommendations, confidence score, reasoning steps) are displayed in the UI. Logs are written to `logs/`.
5. `evaluator.py` runs offline/online tests and saves results to `logs/evaluation_results.json`.

---

## Setup Instructions

### Prerequisites
- Python 3.9+
- An Anthropic API key (for AI features; core scheduling works without one)

### 1. Clone and enter the repo
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your API key (optional, for AI features)
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```
Or enter it directly in the app sidebar at runtime.

### 4. Run the app
```bash
streamlit run app.py
```
Opens at `http://localhost:8501`.

### 5. Run the tests
```bash
# Unit tests only (no API key needed)
python -m pytest

# Unit tests + RAG evaluation (no API key needed)
python evaluator.py

# Full evaluation including live Claude API tests
python evaluator.py --ai
```

---

## Sample Interactions

### Example 1 — Healthy adult dog

**Input:**
- Owner: Jordan, 90 min available
- Pet: Rex, Dog, age 3
- Tasks: Morning Walk (30 min, priority 5), Feeding (10 min, priority 5)

**AI Advisor output (Analyse Schedule):**
```
Recommendations for Rex:
1. Evening Walk (Exercise, 20 min, priority 3, daily) — adult dogs benefit from
   two exercise sessions per day to manage energy and reduce destructive behaviour.
2. Dental Brushing (Medical, 10 min, priority 3, weekly) — dental disease affects
   80% of dogs by age 3; 3x/week brushing significantly reduces risk.
3. Enrichment Play (Enrichment, 15 min, priority 2, daily) — mental stimulation
   via fetch or puzzle feeders prevents boredom and supports emotional health.

Schedule improvement: Add a consistent evening walk at 18:00 to complement the
morning routine. Consistent timing reduces anxiety for Rex.

Confidence: 80%   Sources: dogs, general
```

---

### Example 2 — Senior cat with thyroid medication

**Input:**
- Owner: Sam, 60 min available
- Pet: Mochi, Cat, age 12, special needs: "thyroid medication twice daily"
- Tasks: Thyroid Medication AM (5 min, priority 5, 08:00)

**AI Advisor output (Analyse Schedule):**
```
Recommendations for Mochi:
1. Thyroid Medication PM (Medical, 5 min, priority 5, daily at 20:00) — methimazole
   must be given 12 hours apart to maintain stable blood levels.
2. Interactive Play (Enrichment, 10 min, priority 3, daily) — senior cats benefit
   from gentle daily play to maintain mobility and mental sharpness.
3. Semi-annual Vet Check (Medical, 30 min, priority 4, as needed) — cats 11+ need
   blood tests every 3–6 months to monitor thyroid levels and kidney function.

Schedule improvement: Set a PM medication reminder at 20:00 to match the AM dose
at 08:00. Consistent 12-hour spacing is critical for methimazole effectiveness.

Confidence: 60%   Sources: cats, medical
(Lower confidence because special needs add uncertainty beyond the knowledge base)
```

---

### Example 3 — Quick task suggestions for a new puppy

**Input:**
- Pet: Pip, Dog, age 0, special needs: "8-week-old puppy"
- Action: "Suggest Tasks (quick)"

**AI Advisor output:**
```
Suggested tasks for Pip:
1. Short Play Session — Exercise, 5 min, priority 4, daily
2. Puppy Feeding — Nutrition, 10 min, priority 5, daily (3–4x per day)
3. Socialisation Time — Enrichment, 15 min, priority 5, daily

[Add] button next to each task for one-click addition
```

---

## Design Decisions

| Decision | Rationale |
|---|---|
| Keyword-based RAG over vector embeddings | No external embedding service needed; the knowledge base is small (4 documents); simpler to audit and debug |
| 5-step agentic workflow with visible steps | Users can expand the reasoning panel and see exactly what was retrieved and why — builds trust and debuggability |
| Human-in-the-loop for task suggestions | Tasks are never added without user confirmation; preserves owner control over the schedule |
| Confidence score as heuristic, not ML model | Explainable and testable without training data; directly tied to retrieval quality and schedule health |
| Graceful degradation without API key | Core scheduling always works; AI features degrade to a clear message rather than crashing |
| Structured logging | Makes it possible to audit every AI call, catch errors silently, and review the evaluation trail |

**Trade-offs:**
- Keyword RAG is fast and transparent but will miss semantically similar passages that use different vocabulary.
- The 5-step workflow adds latency (~2–3 sec) compared to a direct API call, but the intermediate steps are valuable for debugging and user trust.
- Confidence scores are heuristic — they should not be treated as calibrated probabilities.

---

## Testing Summary

| Test type | Count | Result |
|---|---|---|
| Unit tests — core system (`test_pawpal.py`) | 36 | 36/36 passed |
| Unit tests — AI agent offline (`test_ai_agent.py`) | 20 | 20/20 passed |
| RAG evaluation — KB retrieval (`evaluator.py`) | 4 | 4/4 passed |
| Agent evaluation — live API (`evaluator.py --ai`) | 4 | 4/4 passed |

**What worked:** Keyword retrieval reliably pulls species-correct documents for standard queries. Confidence scoring drops correctly when schedules have conflicts or pets have special needs. Graceful degradation works cleanly — no crashes or confusing errors when the API key is missing.

**What didn't:** My puppy test expected the exact word "socialization" to appear in Claude's output because it's in the knowledge base. Claude kept paraphrasing it as "expose your puppy to new environments" instead. Had to change the test to check for "socializ" as a partial match. Also, retrieval for exotic pets (rabbits, birds) only returns the general.md fallback, which isn't very useful.

**Confidence:** ★★★★☆ — Core logic and RAG are well covered. The one gap is that live Claude output is verified by keyword checks rather than exact assertions, which is the right call for generative output but means quality is harder to quantify automatically.

---

## Reflection

The part that surprised me most about building this was how much work goes into the stuff around the AI — the retrieval, the confidence score, the logging, the graceful degradation — compared to the actual API call. The Claude call is maybe five lines. Everything else is making sure the system behaves predictably when the retrieval is bad, when the API key is missing, when the schedule is a mess, when the user types something weird into the special needs field.

The human-in-the-loop design ended up being the decision I feel best about. I was tempted to make task suggestions auto-add to the schedule because it would feel smoother. But pet care mistakes have real consequences — a missed medication, an over-exercised dog recovering from surgery, a task that silently disappears from the plan. Making every suggestion require a click to confirm keeps the owner in control without making the feature useless. That felt like the right call.

The confidence score took longer to tune than I expected. I thought it would be a one-line heuristic and it turned out to need real adjustment once I tested it against actual scenarios. A senior cat with medication was scoring 0.1 even when the advice was solid, because the raw penalty math was too aggressive. That's a lesson I'll carry forward: evaluation metrics need to be tested against cases where you already know what the answer should feel like.

See [model_card.md](model_card.md) for the full ethics reflection — limitations, bias, misuse risks, and AI collaboration notes.

---

## Portfolio Note

This project shows that I can take a working system and extend it responsibly — not just by adding a feature, but by thinking through what breaks when AI is involved. I built the retrieval before the API call, the logging before the UI, and the tests before I called anything live. That order matters. It means I understand that an AI feature is only as trustworthy as the scaffolding around it. That's the mindset I want to bring to any AI engineering role.
