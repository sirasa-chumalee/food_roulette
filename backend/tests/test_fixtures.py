"""The committed fixtures must stay parseable by the models that produced them.

The frontend builds every screen against `docs/api/fixtures/` before a live
server exists (ROADMAP §1, Rule 2). If a model changes and these files aren't
regenerated, FE is building against a lie — so this suite fails loudly instead.

    python -m tools.make_contract    # regenerate after any schema change
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app import config, schemas

FIXTURES = config.REPO_ROOT / "docs" / "api" / "fixtures"

RECOMMEND_FIXTURES = [
    "recommend_all_verified.json",
    "recommend_mixed.json",
    "recommend_unverified_only.json",
    "recommend_empty.json",
]

CHAT_FIXTURES = [
    "chat_with_cards.json",
    "chat_no_cards.json",
    "chat_degraded.json",
]


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_openapi_spec_is_committed():
    assert (config.REPO_ROOT / "docs" / "api" / "openapi.yaml").exists()


@pytest.mark.parametrize("name", RECOMMEND_FIXTURES)
def test_recommend_fixture_matches_the_model(name):
    schemas.RecommendOut.model_validate(load(name))


def test_the_four_recommend_cases_are_all_covered():
    """ROADMAP M1 promises FE four states to build against — all four, always."""
    all_verified = schemas.RecommendOut.model_validate(load("recommend_all_verified.json"))
    mixed = schemas.RecommendOut.model_validate(load("recommend_mixed.json"))
    unverified = schemas.RecommendOut.model_validate(load("recommend_unverified_only.json"))
    empty = schemas.RecommendOut.model_validate(load("recommend_empty.json"))

    tiers = lambda out: {c.safety_tier for c in out.recommendations}  # noqa: E731

    assert tiers(all_verified) == {"verified"}
    assert tiers(mixed) == {"verified", "unverified"}
    assert tiers(unverified) == {"unverified"}
    assert unverified.fallback_used is True
    assert empty.recommendations == []


@pytest.mark.parametrize("name", CHAT_FIXTURES)
def test_chat_fixture_matches_the_model(name):
    schemas.ChatOut.model_validate(load(name))


def test_the_three_chat_cases_are_all_covered():
    """ROADMAP M2 promises FE cards, no cards, and a Gemini outage."""
    with_cards = schemas.ChatOut.model_validate(load("chat_with_cards.json"))
    no_cards = schemas.ChatOut.model_validate(load("chat_no_cards.json"))
    degraded = schemas.ChatOut.model_validate(load("chat_degraded.json"))

    assert with_cards.recommendations and with_cards.degraded is None
    assert no_cards.recommendations == []
    # The outage case still carries cards — that's the whole point of it.
    assert degraded.degraded == "LLM_UNAVAILABLE"
    assert degraded.recommendations


def test_the_chat_fixture_reply_stays_grounded():
    """The fixture FE builds its chat bubble from must itself obey the guardrail:
    no restaurant named in `reply` that isn't in `recommendations`."""
    from app.llm import narrate

    with_cards = schemas.ChatOut.model_validate(load("chat_with_cards.json"))
    assert narrate.ungrounded_mentions(with_cards.reply, with_cards.recommendations) == []


@pytest.mark.parametrize("name", ["error_not_found.json", "error_invalid_prefs.json"])
def test_error_fixtures_match_the_envelope(name):
    schemas.ErrorEnvelope.model_validate(load(name))


def test_other_fixtures_match_their_models():
    schemas.SessionOut.model_validate(load("auth_session.json"))
    schemas.PreferencesOut.model_validate(load("preferences.json"))
    assert load("health.json")["status"] == "ok"


def test_every_fixture_file_is_covered_by_this_suite():
    """A new fixture must be asserted on, not just dropped in the folder."""
    known = set(RECOMMEND_FIXTURES) | set(CHAT_FIXTURES) | {
        "auth_session.json",
        "preferences.json",
        "health.json",
        "error_not_found.json",
        "error_invalid_prefs.json",
    }
    on_disk = {p.name for p in Path(FIXTURES).glob("*.json")}
    assert on_disk == known
