"""
Train the AI-Generated Phishing Detection model.

Combines:
1. TF-IDF text features (word patterns)
2. Linguistic/social-engineering features (urgency, authority, financial asks,
   punctuation patterns, sentence uniformity - a lightweight proxy for the
   "too smooth" signal that flags AI-generated text)

Trained on the Enron Spam dataset (17,171 spam / 16,545 ham, real emails).
"""

import re
import string
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from scipy.sparse import hstack, csr_matrix

import os as _os
_BASE_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # project root
DATA_PATH = _os.path.join(_BASE_DIR, "data", "enron_spam_data.csv")
MODEL_DIR = _os.path.join(_BASE_DIR, "models")

# --- Social engineering / urgency lexicons ---
URGENCY_WORDS = [
    "urgent", "immediately", "act now", "expire", "expires", "expiring",
    "suspend", "suspended", "verify", "verify now", "limited time",
    "action required", "final notice", "warning", "alert", "restricted",
    "unusual activity", "click here", "confirm your", "update your",
    "unauthorized", "locked", "security alert"
]

AUTHORITY_WORDS = [
    "bank", "paypal", "amazon", "microsoft", "government", "irs", "tax",
    "official", "support team", "security team", "admin", "administrator",
    "customer service", "billing department"
]

FINANCIAL_WORDS = [
    "payment", "invoice", "refund", "transfer", "wire", "account number",
    "credit card", "ssn", "social security", "password", "pin", "$",
    "won", "prize", "lottery", "inheritance", "free money"
]


def extract_linguistic_features(text: str) -> dict:
    text = str(text) if pd.notna(text) else ""
    text_lower = text.lower()
    words = text.split()
    n_words = max(len(words), 1)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    n_sentences = max(len(sentences), 1)

    # Urgency / authority / financial signal counts (normalized)
    urgency_count = sum(text_lower.count(w) for w in URGENCY_WORDS)
    authority_count = sum(text_lower.count(w) for w in AUTHORITY_WORDS)
    financial_count = sum(text_lower.count(w) for w in FINANCIAL_WORDS)

    # Punctuation / formatting signals
    exclamation_count = text.count("!")
    caps_words = sum(1 for w in words if len(w) > 2 and w.isupper())
    url_count = len(re.findall(r'http[s]?://|www\.', text_lower))

    # "Smoothness" proxy features (AI-generated text tends to be more uniform)
    word_lengths = [len(w.strip(string.punctuation)) for w in words]
    avg_word_len = np.mean(word_lengths) if word_lengths else 0
    std_word_len = np.std(word_lengths) if word_lengths else 0

    sentence_lengths = [len(s.split()) for s in sentences]
    avg_sentence_len = np.mean(sentence_lengths) if sentence_lengths else 0
    std_sentence_len = np.std(sentence_lengths) if sentence_lengths else 0
    # Burstiness: low std relative to mean = unusually uniform (AI-like)
    burstiness = std_sentence_len / (avg_sentence_len + 1e-5)

    return {
        "urgency_count": urgency_count / n_words * 100,
        "authority_count": authority_count / n_words * 100,
        "financial_count": financial_count / n_words * 100,
        "exclamation_count": exclamation_count,
        "caps_word_ratio": caps_words / n_words,
        "url_count": url_count,
        "avg_word_len": avg_word_len,
        "std_word_len": std_word_len,
        "avg_sentence_len": avg_sentence_len,
        "burstiness": burstiness,
        "text_length": len(text),
    }


def main():
    print("Loading data...")
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["Message", "Spam/Ham"])
    df["text"] = df["Subject"].fillna("") + " " + df["Message"].fillna("")
    df["label"] = (df["Spam/Ham"] == "spam").astype(int)  # 1 = phishing/spam, 0 = legit

    # Cap dataset size for speed while keeping balance
    spam_df = df[df["label"] == 1].sample(n=min((df["label"] == 1).sum(), 8000), random_state=42)
    ham_df = df[df["label"] == 0].sample(n=min((df["label"] == 0).sum(), 8000), random_state=42)
    df = pd.concat([spam_df, ham_df]).sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"Using {len(df)} emails ({df['label'].sum()} spam, {len(df) - df['label'].sum()} ham)")

    print("Extracting linguistic features...")
    ling_features = df["text"].apply(extract_linguistic_features).apply(pd.Series)

    print("Building TF-IDF features...")
    tfidf = TfidfVectorizer(max_features=3000, stop_words="english", ngram_range=(1, 2))
    X_tfidf = tfidf.fit_transform(df["text"])

    X_ling = csr_matrix(ling_features.values)
    X = hstack([X_tfidf, X_ling])
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Training Random Forest...")
    clf = RandomForestClassifier(n_estimators=200, max_depth=30, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy: {acc:.4f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred, target_names=["Legit", "Phishing/Spam"]))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    import os
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(clf, f"{MODEL_DIR}/rf_classifier.joblib")
    joblib.dump(tfidf, f"{MODEL_DIR}/tfidf_vectorizer.joblib")
    joblib.dump(list(ling_features.columns), f"{MODEL_DIR}/ling_feature_names.joblib")
    print(f"\nModel saved to {MODEL_DIR}/")


if __name__ == "__main__":
    main()
