# Model Card

## AI Testing Approach

I test the AI coach in two layers: deterministic tests in `tests/test_ai_coach.py` and mocked API-integration tests in `tests/test_gemini_integration.py`. I also keep an optional live Gemini test behind environment flags (`RUN_LIVE_GEMINI_TESTS=1`, `ENABLE_SPECIALIZED_COACH=1`, and `GOOGLE_API_KEY`) to validate real-model behavior separately from fast unit tests.

## Testing Summary

16 tests passed and 1 test was skipped (live Gemini test requires environment flags and API context). The deterministic game-logic and AI-coach tests now consistently return the correct higher/lower direction, including cases where the first model response is reversed. Accuracy improved after adding outcome-specific prompt constraints and a direction-correction retry before fallback.
