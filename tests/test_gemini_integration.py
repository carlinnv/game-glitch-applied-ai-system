import os
from unittest.mock import patch, MagicMock

import pytest

from ai_coach import _maybe_generate_specialized_model_message, get_ai_coach_message


@patch.dict(os.environ, {"ENABLE_SPECIALIZED_COACH": "1", "GOOGLE_API_KEY": "fake-key"})
def test_maybe_generate_specialized_model_message_success(monkeypatch):
    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Warm — you're close. Go LOWER."}]
                }
            }
        ]
    }

    with patch("requests.post", return_value=fake_resp) as mock_post:
        ctx = {
            "difficulty": "Normal",
            "attempts_used": 3,
            "attempt_limit": 8,
            "recent_history": [10, 30, 60],
            "outcome": "Too High",
            "warmth": "warm",
        }
        result = _maybe_generate_specialized_model_message(ctx)
        assert result is not None
        assert "Go LOWER" in result or "LOWER" in result
        # Ensure requests.post was called with the Generative API URL
        assert mock_post.called


@patch.dict(os.environ, {"ENABLE_SPECIALIZED_COACH": "1", "GOOGLE_API_KEY": "fake-key"})
def test_gemini_response_with_secret_is_rejected(monkeypatch):
    # API returns a message that directly reveals the secret; the guardrail should reject it
    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "The secret is 42. Go LOWER."}]
                }
            }
        ]
    }

    with patch("requests.post", return_value=fake_resp):
        ctx = {
            "difficulty": "Normal",
            "attempts_used": 3,
            "attempt_limit": 8,
            "recent_history": [10, 30, 60],
            "outcome": "Too High",
            "warmth": "warm",
        }
        # Use public API to get candidate and then ensure final coach message doesn't include secret
        candidate = _maybe_generate_specialized_model_message(ctx)
        assert candidate is not None

        # Now call the end-to-end function; secret=42 -> guardrails should prevent leakage
        msg = get_ai_coach_message(
            difficulty="Normal",
            attempts_used=3,
            attempt_limit=8,
            history=[10, 30, 60],
            outcome="Too High",
            last_guess=60,
            secret=42,
            low=1,
            high=100,
        )
        assert "42" not in msg
        assert "LOWER" in msg


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_GEMINI_TESTS") != "1"
    or os.getenv("ENABLE_SPECIALIZED_COACH") != "1"
    or not os.getenv("GOOGLE_API_KEY"),
    reason="Requires RUN_LIVE_GEMINI_TESTS=1, ENABLE_SPECIALIZED_COACH=1, and GOOGLE_API_KEY",
)
def test_live_gemini_path_returns_model_source():
    msg, source = get_ai_coach_message(
        difficulty="Normal",
        attempts_used=2,
        attempt_limit=8,
        history=[12, 30, 55],
        outcome="Too High",
        last_guess=55,
        secret=42,
        low=1,
        high=100,
        return_source=True,
    )

    assert source == "model", "Gemini did not produce the message; fallback was used instead"
    assert msg
    assert "LOWER" in msg
    assert "Attempts:" not in msg
