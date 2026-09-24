"""
Basic tests for the feature extraction and prediction pipeline.

Run with:
    cd tests
    python -m pytest test_detector.py -v

Or without pytest:
    python tests/test_detector.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from train_model import extract_linguistic_features
from predict import score_message


def test_urgency_words_detected():
    features = extract_linguistic_features("URGENT: verify your account immediately")
    assert features["urgency_count"] > 0, "Urgency words should be detected"


def test_no_urgency_in_plain_text():
    features = extract_linguistic_features("Here is the report you asked for.")
    assert features["urgency_count"] == 0, "Plain text should not trigger urgency signals"


def test_url_count():
    features = extract_linguistic_features("Click here: http://example.com to continue")
    assert features["url_count"] == 1, "Should detect exactly one URL"


def test_phishing_message_scores_higher_risk():
    phishing = score_message(
        "URGENT: Your account has been suspended. Click here immediately to verify "
        "your identity or lose access permanently: http://secure-bank-verify.com"
    )
    legit = score_message(
        "Hi team, attached is the Q3 report for review before Friday's meeting."
    )
    assert phishing["risk_score"] > legit["risk_score"], (
        "A message using urgency, authority, and a suspicious link should score "
        "a higher risk than a plain, ordinary message"
    )


def test_score_message_returns_expected_keys():
    result = score_message("Hello, just checking in on the project status.")
    expected_keys = {
        "risk_score", "verdict", "flagged_urgency_words",
        "flagged_authority_words", "flagged_financial_words",
        "burstiness", "url_count", "exclamation_count",
    }
    assert expected_keys.issubset(result.keys()), "Response is missing expected fields"


if __name__ == "__main__":
    tests = [
        test_urgency_words_detected,
        test_no_urgency_in_plain_text,
        test_url_count,
        test_phishing_message_scores_higher_risk,
        test_score_message_returns_expected_keys,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {t.__name__} — {e}")
    print(f"\n{passed}/{len(tests)} tests passed")
