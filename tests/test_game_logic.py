import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic_utils import check_guess

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    outcome, message = check_guess(50, 50)
    assert outcome == "Win"

def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    outcome, message = check_guess(60, 50)
    assert outcome == "Too High"

def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    outcome, message = check_guess(40, 50)
    assert outcome == "Too Low"

def test_guessing_bug_hints_not_reversed():
    """
    Test that verifies the guessing bug is fixed.
    The bug: hints were reversed (saying "Go Higher" when guess was too high).
    This test ensures that when guess > secret, it correctly returns "Too High",
    and when guess < secret, it correctly returns "Too Low".
    """
    # When guess is higher than secret, should say "Too High"
    outcome, message = check_guess(75, 50)
    assert outcome == "Too High", "Guess of 75 vs secret 50 should be 'Too High'"
    assert "Go LOWER" in message or "LOWER" in message, "Message should hint to go lower"
    
    # When guess is lower than secret, should say "Too Low"
    outcome, message = check_guess(25, 50)
    assert outcome == "Too Low", "Guess of 25 vs secret 50 should be 'Too Low'"
    assert "Go HIGHER" in message or "HIGHER" in message, "Message should hint to go higher"
    
    # Test with different range values
    outcome, message = check_guess(1, 100)
    assert outcome == "Too Low", "Guess of 1 vs secret 100 should be 'Too Low'"
    
    outcome, message = check_guess(100, 1)
    assert outcome == "Too High", "Guess of 100 vs secret 1 should be 'Too High'"
