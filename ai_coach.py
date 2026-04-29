import os
import requests
from typing import Any, Dict, List, Optional, Tuple, Union
from dotenv import load_dotenv

load_dotenv()

MAX_COACH_CHARS = 600
SYSTEM_POLICY = (
    "You are a game coach. Never reveal the secret number before game over. "
    "Give a short, direct hint that depends on how close the guess is and "
    "whether it is too high or too low. Avoid metaphors, slang, and jokes. "
    "Do not mention attempts, history, or difficulty explicitly."
)


def detect_warmth(last_guess: int, secret: int, low: int, high: int) -> str:
    """Classify how close the latest guess is to the secret."""
    span = max(1, high - low)
    distance = abs(last_guess - secret)

    if distance == 0:
        return "exact"

    ratio = distance / span
    if ratio <= 0.05:
        return "hot"
    if ratio <= 0.15:
        return "warm"
    return "cold"


def _distance_descriptor(last_guess: int, secret: int, low: int, high: int) -> str:
    """Generate a descriptive phrase about how close the guess is to secret."""
    span = max(1, high - low)
    distance = abs(last_guess - secret)

    if distance == 0:
        return ""

    ratio = distance / span
    if ratio <= 0.05:
        return "very close to"
    if ratio <= 0.15:
        return "close to"
    if ratio <= 0.30:
        return "somewhat close to"
    return "fairly far from"


def build_coach_context(
    *,
    difficulty: str,
    attempts_used: int,
    attempt_limit: int,
    history: List[Any],
    outcome: str,
    warmth: str,
    distance_descriptor: str = "",
) -> Dict[str, Any]:
    """Build model-ready context from current game state."""
    return {
        "difficulty": difficulty,
        "attempts_used": attempts_used,
        "attempts_left": max(0, attempt_limit - attempts_used),
        "attempt_limit": attempt_limit,
        "recent_history": history[-5:],
        "outcome": outcome,
        "warmth": warmth,
        "distance_descriptor": distance_descriptor,
    }


def _tone_phrase(*, warmth: str, attempts_used: int, attempt_limit: int) -> str:
    attempts_left = max(0, attempt_limit - attempts_used)

    if attempts_left <= 1:
        return "Last try."
    if warmth == "exact":
        return "Correct."
    if warmth == "hot":
        return "Very close."
    if warmth == "warm":
        return "Close."
    return "A bit off."


def _natural_direction_message(
    *,
    outcome: str,
    warmth: str,
    attempts_used: int,
    attempt_limit: int,
    distance_descriptor: str = "",
) -> str:
    if outcome == "Win":
        return "Correct. Nice work."

    if outcome == "Too High":
        direction_action = "guess lower"
    else:
        direction_action = "guess higher"

    if warmth == "exact":
        return f"Your guess is exact. (This shouldn't happen—you won!)"
    
    if distance_descriptor:
        if outcome == "Win":
            return "Correct. Nice work."
        return f"Your guess is {distance_descriptor} the secret. {direction_action.capitalize()}."
    
    if warmth == "hot":
        return f"Your guess is very close. {direction_action.capitalize()}."
    if warmth == "warm":
        return f"Your guess is close. {direction_action.capitalize()}."
    if attempts_used >= attempt_limit:
        return f"Last try. {direction_action.capitalize()}."
    return f"{direction_action.capitalize()}."


def _maybe_generate_specialized_model_message(
    context: Dict[str, Any],
    *,
    return_reason: bool = False,
    strict_direction: bool = False,
) -> Union[Optional[str], Tuple[Optional[str], str]]:
    """Attempt a REST call to Google Generative API (Gemini) and return the text candidate.

    Controls:
    - ENABLE_SPECIALIZED_COACH=1 to enable.
    - GOOGLE_API_KEY must be set for API-key based auth.
    - GEMINI_MODEL optional model id (default: gemini-2.5-flash-lite).

    This function is conservative: any error or missing creds -> return None so the
    deterministic fallback runs.
    """
    def finish(message: Optional[str], reason: str):
        if return_reason:
            return message, reason
        return message

    if os.getenv("ENABLE_SPECIALIZED_COACH", "0") != "1":
        return finish(None, "disabled")

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        # No API key configured — do not attempt remote call.
        return finish(None, "missing_api_key")

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

    system = SYSTEM_POLICY
    outcome = context.get("outcome")
    distance_descriptor = context.get("distance_descriptor", "")
    distance_hint = f" The guess is {distance_descriptor} the secret." if distance_descriptor else ""
    
    if outcome == "Too High":
        direction_rule = "Indicate they should go lower."
        outcome_rule = "Convey that the guess is too high."
    elif outcome == "Too Low":
        direction_rule = "Indicate they should go higher."
        outcome_rule = "Convey that the guess is too low."
    else:
        direction_rule = "Do not include higher/lower direction."
        outcome_rule = "Provide a brief congratulatory message."
        distance_hint = ""

    strict_note = "" if not strict_direction else " This is a correction pass: fix direction and outcome wording exactly."
    user_prompt = (
        f"Game state:\n"
        f"Difficulty: {context.get('difficulty')}\n"
        f"Attempts left: {context.get('attempts_left')}\n"
        f"Outcome: {outcome}\n"
        f"Warmth: {context.get('warmth')}{distance_hint}\n\n"
        f"Respond with one short, plain-English hint (<= {MAX_COACH_CHARS} chars)."
        f" Be direct and relevant. No metaphors, slang, jokes, filler, or meta phrases like"
        f" 'please provide'."
        f" {outcome_rule} {direction_rule}"
        f" Do NOT reveal the secret number."
        f"{strict_note}"
    )

    # Ensure model name doesn't have 'models/' prefix
    model_name = model.replace("models/", "")
    url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system}\n\n{user_prompt}"}]
            }
        ],
        "generationConfig": {
            "temperature": 0.6,
            "maxOutputTokens": 120,
        },
    }

    try:
        resp = requests.post(url, json=payload, timeout=8)
        if resp.status_code != 200:
            try:
                error_detail = resp.json().get("error", {}).get("message", "")
                return finish(None, f"http_{resp.status_code}: {error_detail}")
            except:
                return finish(None, f"http_{resp.status_code} at {url}")
        data = resp.json()

        # Parse v1 API response format.
        candidate = None
        if isinstance(data, dict):
            # v1 returns 'candidates' list with 'content.parts' structure
            cands = data.get("candidates")
            if cands and isinstance(cands, list) and len(cands) > 0:
                cand = cands[0]
                content = cand.get("content", {})
                parts = content.get("parts", [])
                if parts and isinstance(parts, list):
                    candidate = parts[0].get("text")

        if candidate:
            text = str(candidate).strip()
            if return_reason:
                return text, "model"
            return text

        return finish(None, "no_candidate")
    except Exception as e:
        return finish(None, f"request_exception: {str(e)}")

    return finish(None, "unknown")


def enforce_guardrails(
    *,
    candidate: str,
    outcome: str,
    secret: int,
    max_chars: int = MAX_COACH_CHARS,
) -> Optional[str]:
    """Normalize coach output before returning it."""

    if not candidate or not isinstance(candidate, str):
        return None

    message = " ".join(candidate.split()).strip()
    if not message:
        return None

    return message


def _has_correct_direction(message: str, outcome: str) -> bool:
    lower_message = message.lower()
    if outcome == "Too High":
        return any(
            phrase in lower_message
            for phrase in ("lower", "down", "decrease", "smaller", "less")
        )
    if outcome == "Too Low":
        return any(
            phrase in lower_message
            for phrase in ("higher", "up", "increase", "bigger", "more")
        )
    return True

def get_ai_coach_message(
    *,
    difficulty: str,
    attempts_used: int,
    attempt_limit: int,
    history: List[Any],
    outcome: str,
    last_guess: int,
    secret: int,
    low: int,
    high: int,
    model_message: Optional[str] = None,
    return_source: bool = False,
    return_reason: bool = False,
) -> Union[str, Tuple[str, str], Tuple[str, str, str]]:
    """Get a guarded coach hint from specialized model with deterministic fallback.

    When return_source is True, return (message, source). When return_reason is
    also True, return (message, source, reason) where reason describes why the
    model path failed or what path produced the response.
    """
    warmth = detect_warmth(last_guess=last_guess, secret=secret, low=low, high=high)
    distance_descriptor = _distance_descriptor(last_guess=last_guess, secret=secret, low=low, high=high)
    context = build_coach_context(
        difficulty=difficulty,
        attempts_used=attempts_used,
        attempt_limit=attempt_limit,
        history=history,
        outcome=outcome,
        warmth=warmth,
        distance_descriptor=distance_descriptor,
    )

    fallback_message = _natural_direction_message(
        attempts_used=attempts_used,
        attempt_limit=attempt_limit,
        outcome=outcome,
        distance_descriptor=distance_descriptor,
        warmth=warmth,
    )

    candidate = model_message
    candidate_reason = "provided"
    if candidate is None:
        candidate, candidate_reason = _maybe_generate_specialized_model_message(context, return_reason=True)

    safe_candidate = enforce_guardrails(
        candidate=candidate or fallback_message,
        outcome=outcome,
        secret=secret,
    )
    if safe_candidate is not None:
        if not _has_correct_direction(safe_candidate, outcome):
            # Retry once with stricter direction instructions before using fallback.
            if candidate_reason == "model":
                retry_candidate, retry_reason = _maybe_generate_specialized_model_message(
                    context,
                    return_reason=True,
                    strict_direction=True,
                )
                safe_retry = enforce_guardrails(
                    candidate=retry_candidate or "",
                    outcome=outcome,
                    secret=secret,
                )
                if safe_retry is not None and _has_correct_direction(safe_retry, outcome):
                    safe_candidate = safe_retry
                    candidate_reason = retry_reason
                else:
                    safe_candidate = fallback_message
                    candidate_reason = "direction_mismatch"
            else:
                safe_candidate = fallback_message
                candidate_reason = "direction_mismatch"
        if return_source and return_reason:
            source = "model" if candidate_reason == "model" else "fallback"
            return safe_candidate, source, candidate_reason
        if return_source:
            source = "model" if candidate_reason == "model" else "fallback"
            return safe_candidate, source
        return safe_candidate

    safe_fallback = enforce_guardrails(
        candidate=fallback_message,
        outcome=outcome,
        secret=secret,
    )
    if safe_fallback is not None:
        if return_source and return_reason:
            return safe_fallback, "fallback", "fallback"
        if return_source:
            return safe_fallback, "fallback"
        return safe_fallback

    if outcome == "Too High":
        return ("The number you submitted is too high. Go LOWER.", "last_resort", "last_resort") if return_source and return_reason else (("The number you submitted is too high. Go LOWER.", "last_resort") if return_source else "The number you submitted is too high. Go LOWER.")
    if outcome == "Too Low":
        return ("The number you submitted is too low. Go HIGHER.", "last_resort", "last_resort") if return_source and return_reason else (("The number you submitted is too low. Go HIGHER.", "last_resort") if return_source else "The number you submitted is too low. Go HIGHER.")
    return ("Correct. Nice work.", "last_resort", "last_resort") if return_source and return_reason else (("Correct. Nice work.", "last_resort") if return_source else "Correct. Nice work.")
