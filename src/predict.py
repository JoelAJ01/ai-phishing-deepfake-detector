"""
Score a message for phishing / social-engineering risk.
Combines the RandomForest probability with a human-readable breakdown
of which signals fired (urgency, authority, financial, "too smooth" text).
"""

import joblib
import numpy as np
from scipy.sparse import hstack, csr_matrix

from train_model import (
    extract_linguistic_features, URGENCY_WORDS, AUTHORITY_WORDS, FINANCIAL_WORDS,
    MODEL_DIR
)

_clf = None
_tfidf = None
_ling_feature_names = None


def _load_models():
    global _clf, _tfidf, _ling_feature_names
    if _clf is None:
        _clf = joblib.load(f"{MODEL_DIR}/rf_classifier.joblib")
        _tfidf = joblib.load(f"{MODEL_DIR}/tfidf_vectorizer.joblib")
        _ling_feature_names = joblib.load(f"{MODEL_DIR}/ling_feature_names.joblib")


def score_message(text: str) -> dict:
    _load_models()

    ling = extract_linguistic_features(text)
    ling_vec = np.array([[ling[name] for name in _ling_feature_names]])

    tfidf_vec = _tfidf.transform([text])
    X = hstack([tfidf_vec, csr_matrix(ling_vec)])

    proba = _clf.predict_proba(X)[0]
    risk_score = float(proba[1]) * 100  # probability of phishing/spam

    text_lower = text.lower()
    flagged_urgency = [w for w in URGENCY_WORDS if w in text_lower]
    flagged_authority = [w for w in AUTHORITY_WORDS if w in text_lower]
    flagged_financial = [w for w in FINANCIAL_WORDS if w in text_lower]

    if risk_score >= 75:
        verdict = "HIGH RISK - Likely phishing/social engineering"
    elif risk_score >= 40:
        verdict = "MEDIUM RISK - Suspicious, review carefully"
    else:
        verdict = "LOW RISK - Likely legitimate"

    return {
        "risk_score": round(risk_score, 1),
        "verdict": verdict,
        "flagged_urgency_words": flagged_urgency,
        "flagged_authority_words": flagged_authority,
        "flagged_financial_words": flagged_financial,
        "burstiness": round(ling["burstiness"], 3),
        "url_count": ling["url_count"],
        "exclamation_count": ling["exclamation_count"],
    }


if __name__ == "__main__":
    # Quick manual test
    test_messages = [
        "Hi team, attached is the Q3 report for review before Friday's meeting. Let me know if you have questions.",
        "URGENT: Your account has been suspended due to unusual activity! Click here immediately to verify your identity and avoid permanent suspension: http://secure-bank-verify.com",
        "Dear Customer, we detected unauthorized access to your PayPal account. To restore access, please confirm your payment information within 24 hours or your account will be limited.",
    ]
    for msg in test_messages:
        result = score_message(msg)
        print(f"\nMessage: {msg[:70]}...")
        print(f"Risk Score: {result['risk_score']}% -> {result['verdict']}")
        print(f"Flagged: urgency={result['flagged_urgency_words']}, "
              f"authority={result['flagged_authority_words']}, "
              f"financial={result['flagged_financial_words']}")
