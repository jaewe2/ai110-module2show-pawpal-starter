"""
Unit tests for KnowledgeBase (RAG) and PawPalAgent (offline, no API calls).
These tests run without an Anthropic API key.
"""
from __future__ import annotations

import pytest

from ai_agent import KnowledgeBase, PawPalAgent
from pawpal_system import Owner, Pet, Task


# ---------------------------------------------------------------------------
# KnowledgeBase — retrieval tests
# ---------------------------------------------------------------------------

@pytest.fixture
def kb():
    return KnowledgeBase()


def test_kb_loads_documents(kb):
    assert len(kb.documents) >= 4, "Expected at least 4 knowledge base documents"


def test_kb_retrieve_returns_results(kb):
    results = kb.retrieve("dog exercise walk daily", top_k=3)
    assert len(results) > 0


def test_kb_retrieve_respects_top_k(kb):
    results = kb.retrieve("dog cat pet care", top_k=2)
    assert len(results) <= 2


def test_kb_retrieve_dog_query_surfaces_dogs_doc(kb):
    results = kb.retrieve("dog exercise senior walk daily", top_k=4)
    sources = [r["source"] for r in results]
    assert "dogs" in sources, f"Expected 'dogs' in sources, got {sources}"


def test_kb_retrieve_cat_medication_surfaces_cats_doc(kb):
    results = kb.retrieve("cat thyroid medication senior twice daily", top_k=4)
    sources = [r["source"] for r in results]
    assert "cats" in sources or "medical" in sources, (
        f"Expected 'cats' or 'medical' in sources, got {sources}"
    )


def test_kb_retrieve_dental_health_surfaces_medical(kb):
    results = kb.retrieve("dental teeth brushing disease", top_k=4)
    sources = [r["source"] for r in results]
    assert "medical" in sources or "dogs" in sources or "cats" in sources


def test_kb_retrieve_scores_are_sorted(kb):
    results = kb.retrieve("dog walk exercise", top_k=5)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_kb_retrieve_each_result_has_required_keys(kb):
    results = kb.retrieve("cat feeding litter", top_k=3)
    for r in results:
        assert "source" in r
        assert "content" in r
        assert "score" in r


def test_kb_retrieve_empty_query_returns_empty(kb):
    results = kb.retrieve("", top_k=3)
    assert isinstance(results, list)


def test_kb_retrieve_unrelated_query_returns_low_scores(kb):
    results = kb.retrieve("blockchain quantum computing", top_k=3)
    for r in results:
        assert r["score"] < 0.5, f"Unexpected high score for unrelated query: {r}"


# ---------------------------------------------------------------------------
# PawPalAgent — offline tests (no API key needed)
# ---------------------------------------------------------------------------

@pytest.fixture
def agent_no_key():
    return PawPalAgent(api_key="")


@pytest.fixture
def dog_owner():
    pet = Pet(name="Rex", species="Dog", age=3)
    pet.add_task(Task(name="Walk", category="Exercise", duration_minutes=30, priority=5))
    owner = Owner(name="TestOwner", available_minutes=90, pets=[pet])
    return owner, pet


@pytest.fixture
def cat_owner_senior():
    pet = Pet(name="Mochi", species="Cat", age=12, special_needs="thyroid medication")
    pet.add_task(
        Task(name="Thyroid Med", category="Medical", duration_minutes=5, priority=5, frequency="daily")
    )
    owner = Owner(name="TestOwner", available_minutes=60, pets=[pet])
    return owner, pet


def test_agent_analyze_returns_five_steps(agent_no_key, dog_owner):
    owner, pet = dog_owner
    result = agent_no_key.analyze_schedule(owner, pet)
    assert len(result["steps"]) == 5


def test_agent_analyze_result_has_required_keys(agent_no_key, dog_owner):
    owner, pet = dog_owner
    result = agent_no_key.analyze_schedule(owner, pet)
    for key in ("pet", "steps", "recommendations", "confidence", "sources", "time_remaining"):
        assert key in result, f"Missing key: {key}"


def test_agent_analyze_confidence_in_valid_range(agent_no_key, dog_owner):
    owner, pet = dog_owner
    result = agent_no_key.analyze_schedule(owner, pet)
    assert 0.0 <= result["confidence"] <= 1.0


def test_agent_analyze_senior_cat_lower_confidence(agent_no_key, cat_owner_senior, dog_owner):
    owner_cat, pet_cat = cat_owner_senior
    owner_dog, pet_dog = dog_owner
    result_cat = agent_no_key.analyze_schedule(owner_cat, pet_cat)
    result_dog = agent_no_key.analyze_schedule(owner_dog, pet_dog)
    # Senior cat with special needs should score <= healthy dog
    assert result_cat["confidence"] <= result_dog["confidence"]


def test_agent_analyze_pet_name_in_result(agent_no_key, dog_owner):
    owner, pet = dog_owner
    result = agent_no_key.analyze_schedule(owner, pet)
    assert result["pet"] == pet.name


def test_agent_analyze_time_remaining_is_integer(agent_no_key, dog_owner):
    owner, pet = dog_owner
    result = agent_no_key.analyze_schedule(owner, pet)
    assert isinstance(result["time_remaining"], int)


def test_agent_analyze_sources_list(agent_no_key, dog_owner):
    owner, pet = dog_owner
    result = agent_no_key.analyze_schedule(owner, pet)
    assert isinstance(result["sources"], list)


def test_agent_analyze_no_api_key_graceful(agent_no_key, dog_owner):
    """Agent should not raise when no API key is set — recommendations degrade gracefully."""
    owner, pet = dog_owner
    result = agent_no_key.analyze_schedule(owner, pet)
    assert "unavailable" in result["recommendations"].lower() or len(result["recommendations"]) > 0


def test_agent_suggest_tasks_no_key_returns_empty(agent_no_key, dog_owner):
    owner, pet = dog_owner
    result = agent_no_key.suggest_tasks(pet, owner)
    assert result["tasks"] == []
    assert isinstance(result["sources"], list)


def test_agent_confidence_decreases_with_conflicts(agent_no_key):
    """Adding schedule conflicts should reduce confidence score."""
    pet = Pet(name="Buddy", species="Dog", age=4)
    pet.add_task(Task(name="Walk", category="Exercise", duration_minutes=20, priority=5, start_time="08:00"))
    pet.add_task(Task(name="Feed", category="Nutrition", duration_minutes=10, priority=5, start_time="08:00"))
    owner_conflict = Owner(name="Test", available_minutes=90, pets=[pet])

    pet2 = Pet(name="Buddy2", species="Dog", age=4)
    pet2.add_task(Task(name="Walk", category="Exercise", duration_minutes=20, priority=5, start_time="07:00"))
    pet2.add_task(Task(name="Feed", category="Nutrition", duration_minutes=10, priority=5, start_time="08:00"))
    owner_clean = Owner(name="Test", available_minutes=90, pets=[pet2])

    result_conflict = agent_no_key.analyze_schedule(owner_conflict, pet)
    result_clean = agent_no_key.analyze_schedule(owner_clean, pet2)

    assert result_conflict["confidence"] <= result_clean["confidence"]
