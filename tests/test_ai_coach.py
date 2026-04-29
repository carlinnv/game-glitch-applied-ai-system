import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_coach import detect_warmth, enforce_guardrails, get_ai_coach_message, SYSTEM_POLICY


def test_detect_warmth_hot_warm_cold():
    assert detect_warmth(last_guess=50, secret=50, low=1, high=100) == "exact"
    assert detect_warmth(last_guess=52, secret=50, low=1, high=100) == "hot"
    assert detect_warmth(last_guess=60, secret=50, low=1, high=100) == "warm"
    assert detect_warmth(last_guess=90, secret=50, low=1, high=100) == "cold"


def test_guardrail_requires_directional_clue_for_too_high_and_too_low():
    high_msg = enforce_guardrails(
        candidate="The number you submitted is too high. Go LOWER.",
        outcome="Too High",
        secret=77,
    )
    low_msg = enforce_guardrails(
        candidate="The number you submitted is too low. Go HIGHER.",
        outcome="Too Low",
        secret=77,
    )

    assert high_msg is not None
    assert high_msg.startswith("The number you submitted is too high.")
    assert low_msg is not None
    assert low_msg.startswith("The number you submitted is too low.")


def test_guardrail_rejects_secret_reveal_and_falls_back():
    msg = get_ai_coach_message(
        difficulty="Normal",
        attempts_used=3,
        attempt_limit=8,
        history=[12, 40, 72],
        outcome="Too High",
        last_guess=72,
        secret=64,
        low=1,
        high=100,
        model_message="The secret is 64. Go lower next.",
    )

    assert "64" not in msg
    assert "LOWER" in msg


def test_guardrail_rejects_prompt_like_filler():
    msg = get_ai_coach_message(
        difficulty="Normal",
        attempts_used=3,
        attempt_limit=8,
        history=[12, 40, 72],
        outcome="Too Low",
        last_guess=72,
        secret=64,
        low=1,
        high=100,
        model_message="Please provide the Go HIGHER.",
    )

    assert msg == "The number you submitted is too low. Go HIGHER."


def test_guardrail_rejects_max_length():
    very_long = "a" * 1000
    guarded = enforce_guardrails(candidate=very_long, outcome="Too Low", secret=42, max_chars=120)
    assert guarded is None


def test_system_policy_present_for_model_integration():
    assert "Never reveal the secret number" in SYSTEM_POLICY


@patch.dict(os.environ, {"ENABLE_SPECIALIZED_COACH": "0"})
def test_coach_message_is_short_and_tone_driven():
    msg = get_ai_coach_message(
        difficulty="Hard",
        attempts_used=4,
        attempt_limit=5,
        history=[10, 15, 30, 41],
        outcome="Too Low",
        last_guess=41,
        secret=45,
        low=1,
        high=50,
    )

    assert msg == "The number you submitted is too low. Go HIGHER."
    assert "Attempts:" not in msg
    assert "Recent guesses:" not in msg
    assert "Difficulty:" not in msg
    assert "You are" not in msg
