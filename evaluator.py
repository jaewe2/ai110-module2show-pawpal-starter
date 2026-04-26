"""
PawPal+ Evaluation Suite
Runs predefined test scenarios to measure RAG retrieval accuracy and AI
recommendation quality. Run without --ai for fast, offline KB tests only.
Run with --ai to include live Claude API tests (requires ANTHROPIC_API_KEY).
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from pawpal_system import Owner, Pet, Task
from ai_agent import KnowledgeBase, PawPalAgent

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_DIR / "evaluation.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Test scenarios
# ---------------------------------------------------------------------------

KB_SCENARIOS = [
    {
        "id": "KB001",
        "name": "Dog exercise retrieval",
        "query": "dog exercise walk daily senior",
        "expected_sources": ["dogs", "general"],
        "description": "RAG should surface dog-specific and general care documents",
    },
    {
        "id": "KB002",
        "name": "Cat thyroid medication retrieval",
        "query": "cat thyroid medication senior twice daily",
        "expected_sources": ["cats", "medical"],
        "description": "RAG should surface cat and medical documents for medication queries",
    },
    {
        "id": "KB003",
        "name": "General multi-pet time management",
        "query": "multiple pets time management schedule priority",
        "expected_sources": ["general"],
        "description": "RAG should surface general care document for scheduling queries",
    },
    {
        "id": "KB004",
        "name": "Dental health retrieval",
        "query": "dental teeth brushing dog cat disease",
        "expected_sources": ["medical", "dogs", "cats"],
        "description": "Dental queries should surface medical and species-specific docs",
    },
]

AGENT_SCENARIOS = [
    {
        "id": "AG001",
        "name": "Healthy adult dog, no tasks",
        "pet_kwargs": {"name": "Rex", "species": "Dog", "age": 3},
        "tasks": [],
        "owner_minutes": 90,
        "expected_keywords": ["walk", "feed", "exercise", "play"],
        "description": "Should recommend basic daily tasks for a healthy adult dog",
    },
    {
        "id": "AG002",
        "name": "Senior cat with thyroid medication",
        "pet_kwargs": {"name": "Mochi", "species": "Cat", "age": 12, "special_needs": "thyroid medication twice daily"},
        "tasks": [
            Task(name="Thyroid Medication AM", category="Medical", duration_minutes=5, priority=5, frequency="daily", start_time="08:00"),
        ],
        "owner_minutes": 60,
        "expected_keywords": ["medication", "thyroid", "senior", "vet"],
        "description": "Should emphasise special medical needs and senior care",
    },
    {
        "id": "AG003",
        "name": "Over-budget schedule with conflict",
        "pet_kwargs": {"name": "Buddy", "species": "Dog", "age": 5},
        "tasks": [
            Task(name="Morning Walk", category="Exercise", duration_minutes=30, priority=5, start_time="08:00"),
            Task(name="Feeding", category="Nutrition", duration_minutes=10, priority=5, start_time="08:00"),
        ],
        "owner_minutes": 25,
        "expected_keywords": ["conflict", "time", "priority", "schedule"],
        "description": "Should flag conflicts and limited time budget",
    },
    {
        "id": "AG004",
        "name": "Young puppy",
        "pet_kwargs": {"name": "Pip", "species": "Dog", "age": 0, "special_needs": "8-week-old puppy"},
        "tasks": [],
        "owner_minutes": 120,
        "expected_keywords": ["puppy", "short", "socializ", "young"],
        "description": "Should recommend age-appropriate puppy care",
    },
]

# ---------------------------------------------------------------------------
# Test runners
# ---------------------------------------------------------------------------

def run_kb_test(kb: KnowledgeBase, scenario: dict) -> dict:
    retrieved = kb.retrieve(scenario["query"], top_k=4)
    sources = [r["source"] for r in retrieved]
    hit = any(s in sources for s in scenario["expected_sources"])
    return {
        "id": scenario["id"],
        "name": scenario["name"],
        "passed": hit,
        "retrieved_sources": sources,
        "expected_sources": scenario["expected_sources"],
        "description": scenario["description"],
        "type": "RAG",
    }


def run_agent_test(agent: PawPalAgent, scenario: dict) -> dict:
    pet = Pet(**scenario["pet_kwargs"])
    for task in scenario["tasks"]:
        pet.add_task(task)
    owner = Owner(name="Evaluator", available_minutes=scenario["owner_minutes"], pets=[pet])

    result = agent.analyze_schedule(owner, pet)
    recs_lower = result["recommendations"].lower()

    keyword_hits = [k for k in scenario["expected_keywords"] if k in recs_lower]
    confidence = result["confidence"]
    steps_ok = len(result["steps"]) == 5
    passed = len(keyword_hits) > 0 and confidence > 0.2 and steps_ok

    return {
        "id": scenario["id"],
        "name": scenario["name"],
        "passed": passed,
        "confidence": confidence,
        "keyword_hits": keyword_hits,
        "expected_keywords": scenario["expected_keywords"],
        "steps_completed": len(result["steps"]),
        "description": scenario["description"],
        "type": "Agent",
    }


# ---------------------------------------------------------------------------
# Main evaluation runner
# ---------------------------------------------------------------------------

def run_evaluation(use_ai: bool = False) -> dict:
    """
    Run the full evaluation suite.
    KB tests always run; Agent tests only run when use_ai=True.
    """
    border = "=" * 62
    print(f"\n{border}")
    print("  PawPal+ AI Evaluation Suite")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Mode: {'KB + Agent (live API)' if use_ai else 'KB only (offline)'}")
    print(border)

    kb = KnowledgeBase()
    results: list[dict] = []

    # --- KB / RAG tests (no API needed) ---
    print(f"\n[RAG] Running {len(KB_SCENARIOS)} knowledge-base tests...")
    for s in KB_SCENARIOS:
        r = run_kb_test(kb, s)
        results.append(r)
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['id']}: {r['name']}")
        if not r["passed"]:
            print(f"         Expected: {r['expected_sources']} | Got: {r['retrieved_sources']}")

    # --- Agent tests (require API key) ---
    if use_ai:
        agent = PawPalAgent()
        print(f"\n[Agent] Running {len(AGENT_SCENARIOS)} agent tests...")
        for s in AGENT_SCENARIOS:
            try:
                r = run_agent_test(agent, s)
                results.append(r)
                status = "PASS" if r["passed"] else "FAIL"
                conf = r.get("confidence", 0.0)
                hits = r.get("keyword_hits", [])
                print(f"  [{status}] {r['id']}: {r['name']} (conf={conf:.2f}, hits={hits})")
            except Exception as exc:
                results.append(
                    {"id": s["id"], "name": s["name"], "passed": False, "error": str(exc), "type": "Agent"}
                )
                print(f"  [ERROR] {s['id']}: {s['name']} — {exc}")
    else:
        print("\n[Agent] Skipped — run with --ai flag to include live API tests")

    # --- Summary ---
    passed = sum(1 for r in results if r.get("passed"))
    total = len(results)
    pct = int(passed / total * 100) if total else 0
    conf_scores = [r["confidence"] for r in results if "confidence" in r]
    avg_conf = round(sum(conf_scores) / len(conf_scores), 2) if conf_scores else None

    print(f"\n{border}")
    print(f"  Results : {passed}/{total} passed ({pct}%)")
    if avg_conf is not None:
        print(f"  Avg confidence (agent tests): {avg_conf}")
    if pct == 100:
        print("  Status  : ALL TESTS PASSED ✓")
    elif pct >= 75:
        print("  Status  : MOSTLY PASSING — review failures above")
    else:
        print("  Status  : NEEDS ATTENTION — multiple failures")
    print(border + "\n")

    summary = {
        "timestamp": datetime.now().isoformat(),
        "mode": "kb+agent" if use_ai else "kb_only",
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate_pct": pct,
        "avg_confidence": avg_conf,
        "results": results,
    }

    out_path = LOG_DIR / "evaluation_results.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Full results saved to {out_path}")
    return summary


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_evaluation(use_ai="--ai" in sys.argv)
