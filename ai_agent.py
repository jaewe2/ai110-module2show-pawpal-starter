"""
PawPal+ AI Agent
Combines RAG (keyword-based retrieval from a local knowledge base) with the
Claude API to deliver a 5-step agentic workflow for pet care recommendations.
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

import anthropic

from pawpal_system import VALID_CATEGORIES, VALID_FREQUENCIES, Owner, Pet, Scheduler, Task

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "pawpal_agent.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Knowledge Base — simple keyword-based RAG retriever
# ---------------------------------------------------------------------------

class KnowledgeBase:
    """Loads markdown documents from knowledge_base/ and retrieves relevant chunks."""

    def __init__(self, kb_dir: str = "knowledge_base"):
        self.documents: dict[str, str] = {}
        self._load(Path(kb_dir))

    def _load(self, kb_path: Path) -> None:
        if not kb_path.exists():
            logger.warning("Knowledge base directory not found: %s", kb_path)
            return
        for md_file in sorted(kb_path.glob("*.md")):
            self.documents[md_file.stem] = md_file.read_text()
        logger.info("Loaded %d knowledge base documents: %s", len(self.documents), list(self.documents))

    def retrieve(self, query: str, top_k: int = 4) -> list[dict]:
        """
        Return the top-k most relevant paragraphs across all documents.
        Relevance = keyword overlap between query words and paragraph words.
        """
        query_words = set(re.sub(r"[^a-z0-9 ]", "", query.lower()).split())
        scored: list[dict] = []

        for doc_name, content in self.documents.items():
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            for para in paragraphs:
                para_words = set(re.sub(r"[^a-z0-9 ]", "", para.lower()).split())
                overlap = len(query_words & para_words)
                if overlap > 0:
                    scored.append(
                        {
                            "source": doc_name,
                            "content": para,
                            "score": overlap / max(len(query_words), 1),
                        }
                    )

        scored.sort(key=lambda x: x["score"], reverse=True)
        top = scored[:top_k]
        logger.info(
            "RAG retrieved %d chunks for query '%s': sources=%s",
            len(top),
            query[:60],
            [r["source"] for r in top],
        )
        return top


# ---------------------------------------------------------------------------
# PawPal Agent — agentic workflow + Claude API
# ---------------------------------------------------------------------------

class PawPalAgent:
    """
    5-step agentic reasoning:
      1. Analyse pet profile
      2. Retrieve relevant knowledge (RAG)
      3. Evaluate current schedule and conflicts
      4. Generate personalised recommendations via Claude
      5. Validate recommendations against time budget
    """

    MODEL = "claude-opus-4-7"

    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.demo_mode = key == "demo"
        if self.demo_mode:
            self.client = None
            logger.info("PawPalAgent running in DEMO MODE")
        elif not key:
            self.client = None
            logger.warning("ANTHROPIC_API_KEY not set — AI features will be unavailable")
        else:
            self.client = anthropic.Anthropic(api_key=key)
        self.kb = KnowledgeBase()
        logger.info("PawPalAgent initialised (model=%s)", self.MODEL)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _pet_context(self, pet: Pet, owner: Owner) -> str:
        scheduler = Scheduler(owner)
        pending = scheduler.filter_tasks(pet_name=pet.name, completed=False)
        task_lines = "\n".join(
            f"  - {t.name} ({t.category}, {t.duration_minutes} min, priority {t.priority}, {t.frequency})"
            for _, t in pending
        ) or "  (no tasks yet)"
        return (
            f"Pet: {pet.get_summary()}\n"
            f"Current pending tasks:\n{task_lines}\n"
            f"Owner's daily time budget: {owner.available_minutes} minutes"
        )

    # Patterns that indicate prompt injection attempts in user-supplied text
    _INJECTION_PATTERNS = re.compile(
        r"(ignore (all |previous |above |prior )?instructions?|"
        r"system\s*:|assistant\s*:|<\s*/?system\s*>|"
        r"disregard|forget (everything|all)|new instructions?)",
        re.IGNORECASE,
    )

    def _guard_input(self, text: str, field: str = "input") -> str:
        """Truncate oversized strings and strip prompt-injection patterns."""
        if len(text) > 2000:
            logger.warning("Input field '%s' truncated from %d chars", field, len(text))
            text = text[:2000] + " [truncated]"
        if self._INJECTION_PATTERNS.search(text):
            logger.warning("Potential prompt injection detected in field '%s' — stripped", field)
            text = self._INJECTION_PATTERNS.sub("[removed]", text)
        return text

    def _demo_recommendations(self, pet: Pet) -> str:
        species = pet.species.lower()
        if species == "dog":
            return (
                "**1. Morning Exercise Walk (30 min)**\n"
                "Daily walks are essential for cardiovascular health and mental stimulation. "
                "Aim for at least 30 minutes in the morning to set a calm tone for the day.\n\n"
                "**2. Interactive Feeding (10 min)**\n"
                "Use a puzzle feeder or scatter kibble in the yard to slow eating and provide "
                "enrichment. This reduces boredom and supports healthy digestion.\n\n"
                "**3. Evening Grooming Check (5 min)**\n"
                "A quick daily brush and paw check prevents matting, detects skin issues early, "
                "and strengthens the bond between you and your dog.\n\n"
                "**Schedule tip:** Cluster the walk and feeding within the same morning block "
                "to build a consistent routine your dog can anticipate."
            )
        elif species == "cat":
            return (
                "**1. Play Session (15 min)**\n"
                "Interactive wand or feather toy play mimics hunting behaviour and prevents "
                "obesity. Two sessions per day — morning and evening — works best.\n\n"
                "**2. Litter Box Check (5 min)**\n"
                "Scoop daily and do a full clean weekly. Cats are fastidious; a dirty box "
                "leads to avoidance and stress-related behaviours.\n\n"
                "**3. Grooming Brush (5 min)**\n"
                "Regular brushing reduces hairballs and gives you a chance to check for "
                "lumps, fleas, or coat changes.\n\n"
                "**Schedule tip:** Keep feeding times consistent — cats regulate appetite "
                "better on a fixed twice-daily schedule."
            )
        else:
            return (
                "**1. Daily Health Check (5 min)**\n"
                "Observe eyes, coat, appetite, and behaviour each morning. Early detection "
                "of changes is the most effective preventive care.\n\n"
                "**2. Enrichment Activity (15 min)**\n"
                "Species-appropriate enrichment (foraging, toys, exploration) reduces stress "
                "and supports cognitive health.\n\n"
                "**3. Scheduled Feeding (10 min)**\n"
                "Consistent meal times support digestive health and let you monitor appetite "
                "changes that may signal illness.\n\n"
                "**Schedule tip:** Group care tasks into one morning and one evening block "
                "to minimise disruption to your pet's routine."
            )

    def _demo_tasks(self, pet: Pet) -> list[dict]:
        species = pet.species.lower()
        if species == "dog":
            return [
                {"name": "Morning Walk", "category": "Exercise", "duration_minutes": 30, "priority": 4, "frequency": "daily"},
                {"name": "Puzzle Feeder", "category": "Enrichment", "duration_minutes": 10, "priority": 3, "frequency": "daily"},
                {"name": "Evening Brush", "category": "Grooming", "duration_minutes": 5, "priority": 2, "frequency": "daily"},
            ]
        elif species == "cat":
            return [
                {"name": "Wand Play Session", "category": "Enrichment", "duration_minutes": 15, "priority": 4, "frequency": "daily"},
                {"name": "Litter Box Scoop", "category": "Other", "duration_minutes": 5, "priority": 5, "frequency": "daily"},
                {"name": "Coat Brushing", "category": "Grooming", "duration_minutes": 5, "priority": 2, "frequency": "daily"},
            ]
        else:
            return [
                {"name": "Health Check", "category": "Medical", "duration_minutes": 5, "priority": 4, "frequency": "daily"},
                {"name": "Enrichment Activity", "category": "Enrichment", "duration_minutes": 15, "priority": 3, "frequency": "daily"},
                {"name": "Scheduled Feeding", "category": "Nutrition", "duration_minutes": 10, "priority": 5, "frequency": "daily"},
            ]

    def _validate_ai_task(self, t: object) -> bool:
        """Return True only if an AI-generated task dict has all required keys and valid values."""
        if not isinstance(t, dict):
            return False
        required = {"name", "category", "duration_minutes", "priority", "frequency"}
        if not required.issubset(t):
            return False
        if not isinstance(t["name"], str) or not t["name"].strip():
            return False
        if t["category"] not in VALID_CATEGORIES:
            return False
        if not isinstance(t["duration_minutes"], int) or not (1 <= t["duration_minutes"] <= 240):
            return False
        if not isinstance(t["priority"], int) or not (1 <= t["priority"] <= 5):
            return False
        if t["frequency"] not in VALID_FREQUENCIES:
            return False
        return True

    def _score_confidence(
        self, retrieved: list[dict], pet: Pet, conflicts: list[str]
    ) -> float:
        """
        Heuristic confidence score (0.0–1.0):
          +0.1 per retrieved chunk (up to +0.3)
          -0.1 if pet has special needs (less certain)
          -0.1 per conflict (up to -0.2)
        """
        score = 0.5
        score += min(len(retrieved) * 0.1, 0.3)
        if pet.special_needs:
            score -= 0.1
        score -= min(len(conflicts) * 0.1, 0.2)
        return round(max(0.0, min(1.0, score)), 2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_schedule(self, owner: Owner, pet: Pet) -> dict:
        """
        Run the full 5-step agentic workflow for a given pet.
        Returns a result dict with steps, recommendations, confidence, and sources.
        """
        logger.info("=== Starting schedule analysis for '%s' ===", pet.name)
        steps: list[dict] = []

        # Step 1 — Analyse pet profile
        profile_summary = self._guard_input(pet.get_summary(), "pet_summary")
        steps.append({"step": 1, "action": "Analyse pet profile", "result": profile_summary})
        logger.info("Step 1 complete: %s", profile_summary)

        # Step 2 — Retrieve from knowledge base (RAG)
        query = self._guard_input(
            f"{pet.species} age {pet.age} {pet.special_needs} care exercise feeding grooming",
            "rag_query",
        )
        retrieved = self.kb.retrieve(query, top_k=4)
        context_text = "\n\n".join(
            f"[{r['source']}] {r['content']}" for r in retrieved
        ) or "No specific knowledge retrieved."
        steps.append(
            {
                "step": 2,
                "action": "Retrieve knowledge base (RAG)",
                "result": f"Retrieved {len(retrieved)} relevant passage(s)",
                "sources": [r["source"] for r in retrieved],
            }
        )
        logger.info("Step 2 complete: %d passages retrieved", len(retrieved))

        # Step 3 — Evaluate current schedule
        scheduler = Scheduler(owner)
        plan = scheduler.generate_plan()
        pet_plan = [(p, t) for p, t in plan if p.name == pet.name]
        conflicts = scheduler.detect_conflicts()
        steps.append(
            {
                "step": 3,
                "action": "Evaluate current schedule",
                "result": (
                    f"{len(pet_plan)} task(s) in today's plan; "
                    f"{len(conflicts)} scheduling conflict(s) detected"
                ),
            }
        )
        logger.info("Step 3 complete: %d tasks planned, %d conflicts", len(pet_plan), len(conflicts))

        # Step 4 — Generate recommendations via Claude
        if self.demo_mode:
            ai_text = self._demo_recommendations(pet)
            logger.info("Step 4 complete: demo recommendations returned")
        elif self.client is None:
            ai_text = (
                "AI recommendations unavailable — please set the ANTHROPIC_API_KEY "
                "environment variable and restart the app."
            )
            logger.warning("Skipping Claude API call — no API key")
        else:
            pet_ctx = self._guard_input(self._pet_context(pet, owner), "pet_context")
            conflict_text = "\n".join(conflicts) if conflicts else "No conflicts detected."
            prompt = (
                "You are a professional pet care advisor. "
                "Use the retrieved knowledge and the pet's profile to give specific, "
                "actionable advice.\n\n"
                f"RETRIEVED PET CARE KNOWLEDGE:\n{context_text}\n\n"
                f"PET PROFILE AND SCHEDULE:\n{pet_ctx}\n\n"
                f"SCHEDULE ISSUES:\n{conflict_text}\n\n"
                "Provide:\n"
                "1. 2–3 specific task recommendations (name, category, duration, priority)\n"
                "2. One schedule improvement suggestion\n"
                "3. Brief explanation of why these matter for this specific pet\n\n"
                "Be concise and practical."
            )
            try:
                response = self.client.messages.create(
                    model=self.MODEL,
                    max_tokens=600,
                    system=(
                        "You are a knowledgeable, caring pet care advisor. "
                        "Give practical, specific advice tailored to the pet's species, age, and needs."
                    ),
                    messages=[{"role": "user", "content": prompt}],
                )
                ai_text = response.content[0].text
                logger.info("Step 4 complete: Claude responded (%d chars)", len(ai_text))
            except anthropic.APIError as exc:
                ai_text = f"AI recommendations unavailable: {exc}"
                logger.error("Claude API error: %s", exc)

        steps.append({"step": 4, "action": "Generate AI recommendations", "result": ai_text})

        # Step 5 — Validate against time budget
        used = sum(t.duration_minutes for _, t in pet_plan)
        remaining = owner.available_minutes - used
        steps.append(
            {
                "step": 5,
                "action": "Validate against time budget",
                "result": (
                    f"{used} min used, {remaining} min remaining "
                    f"(budget: {owner.available_minutes} min)"
                ),
            }
        )
        logger.info("Step 5 complete: %d min remaining", remaining)

        confidence = self._score_confidence(retrieved, pet, conflicts)
        logger.info(
            "=== Analysis complete for '%s' | confidence=%.2f ===", pet.name, confidence
        )

        return {
            "pet": pet.name,
            "steps": steps,
            "recommendations": ai_text,
            "confidence": confidence,
            "sources": list({r["source"] for r in retrieved}),
            "time_remaining": remaining,
        }

    def suggest_tasks(self, pet: Pet, owner: Owner) -> dict:
        """
        Quick task suggestion (no full agentic loop).
        Returns a list of Task-compatible dicts based on RAG + Claude.
        """
        logger.info("Suggesting tasks for '%s'", pet.name)
        query = self._guard_input(
            f"{pet.species} age {pet.age} essential daily tasks care",
            "suggest_query",
        )
        retrieved = self.kb.retrieve(query, top_k=3)
        context = "\n\n".join(r["content"] for r in retrieved)

        if self.demo_mode:
            logger.info("suggest_tasks: returning demo tasks for '%s'", pet.name)
            return {"tasks": self._demo_tasks(pet), "sources": [r["source"] for r in retrieved]}
        if self.client is None:
            logger.warning("No API key — returning empty task suggestions")
            return {"tasks": [], "sources": []}

        prompt = (
            "Based on the pet care knowledge below and the pet's profile, "
            "suggest exactly 3 essential care tasks.\n\n"
            f"PET CARE KNOWLEDGE:\n{context}\n\n"
            f"PET: {pet.get_summary()}\n\n"
            "Return ONLY a JSON array with exactly 3 objects, each with keys: "
            "name (str), category (Exercise|Nutrition|Medical|Grooming|Enrichment|Other), "
            "duration_minutes (int), priority (1–5 int), frequency (daily|weekly|as needed).\n"
            "No extra text — JSON array only."
        )

        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                tasks_data = json.loads(match.group())
                valid = [t for t in tasks_data if self._validate_ai_task(t)]
                logger.info("Suggested %d tasks for '%s'", len(valid), pet.name)
                return {"tasks": valid, "sources": [r["source"] for r in retrieved]}
        except (anthropic.APIError, json.JSONDecodeError, ValueError) as exc:
            logger.error("suggest_tasks error: %s", exc)

        return {"tasks": [], "sources": [r["source"] for r in retrieved]}
