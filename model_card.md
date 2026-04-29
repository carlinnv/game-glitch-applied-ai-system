# Model Card

## AI Testing Approach

I test the AI coach in two layers: deterministic tests in `tests/test_ai_coach.py` and mocked API-integration tests in `tests/test_gemini_integration.py`. I also keep an optional live Gemini test behind environment flags (`RUN_LIVE_GEMINI_TESTS=1`, `ENABLE_SPECIALIZED_COACH=1`, and `GOOGLE_API_KEY`) to validate real-model behavior separately from fast unit tests.

## Testing Summary

16 tests passed and 1 test was skipped (live Gemini test requires environment flags and API context). The deterministic game-logic and AI-coach tests now consistently return the correct higher/lower direction, including cases where the first model response is reversed. Accuracy improved after adding outcome-specific prompt constraints and a direction-correction retry before fallback.

## Reflection

My system is limited by prompt sensitivity and model variability, so the same game state can still produce different wording quality across runs. A key bias is style bias: the coach tends to overuse certain phrasing patterns and can prioritize fluent wording over precise direction unless constrained. This AI could be misused by revealing the secret number or giving intentionally misleading hints, so I reduce risk by validating direction against game outcome, using retry logic, and keeping deterministic last-resort hints when output quality drops.

What surprised me most during reliability testing was how often small prompt wording changes affected directional accuracy, even when the underlying game logic was correct. My collaboration with AI was strongest when I used it for iterative debugging and test generation: one helpful suggestion was to separate logic into utility functions and add targeted tests for reversed hint direction. One flawed suggestion was over-relaxing guardrails to pass through nearly all model text, which reduced safety and let incorrect or overly loose responses through until I reintroduced direction validation.
