"""
SecureDroid - ML Model Training Script
Trains both Naive Bayes and Random Forest classifiers on Android permission data.
"""

import numpy as np
import pandas as pd
import joblib
import json
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (classification_report, confusion_matrix,
                              accuracy_score, roc_auc_score)
from sklearn.preprocessing import LabelEncoder

# ─────────────────────────────────────────────
# Feature definitions (18 permission features)
# ─────────────────────────────────────────────
FEATURE_NAMES = [
    "READ_CONTACTS",
    "WRITE_CONTACTS",
    "READ_SMS",
    "SEND_SMS",
    "RECEIVE_SMS",
    "READ_CALL_LOG",
    "CAMERA",
    "RECORD_AUDIO",
    "ACCESS_FINE_LOCATION",
    "ACCESS_COARSE_LOCATION",
    "READ_EXTERNAL_STORAGE",
    "WRITE_EXTERNAL_STORAGE",
    "INTERNET",
    "RECEIVE_BOOT_COMPLETED",
    "PROCESS_OUTGOING_CALLS",
    "ACCESS_NETWORK_STATE",
    "FOREGROUND_SERVICE",
    "num_permissions",
]

DANGEROUS_PERMISSIONS = [
    "READ_CONTACTS", "WRITE_CONTACTS", "READ_SMS", "SEND_SMS",
    "RECEIVE_SMS", "READ_CALL_LOG", "CAMERA", "RECORD_AUDIO",
    "ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION",
    "READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE",
    "PROCESS_OUTGOING_CALLS",
]


def generate_synthetic_dataset(n_samples=2000, random_state=42):
    """
    Generate a realistic synthetic dataset of Android app permission patterns.
    Benign apps:  low dangerous permissions, typical utility features.
    Malware apps: high dangerous permissions, SMS/CALL/LOCATION abuse.
    """
    rng = np.random.default_rng(random_state)
    rows = []

    half = n_samples // 2

    # ── Benign apps ──────────────────────────────────────────────────────────
    for _ in range(half):
        row = {f: 0 for f in FEATURE_NAMES}
        # Typical benign pattern: uses INTERNET + maybe CAMERA/LOCATION
        row["INTERNET"] = 1
        row["ACCESS_NETWORK_STATE"] = 1
        if rng.random() < 0.4:
            row["CAMERA"] = 1
        if rng.random() < 0.3:
            row["ACCESS_FINE_LOCATION"] = 1
        if rng.random() < 0.2:
            row["READ_EXTERNAL_STORAGE"] = 1
        if rng.random() < 0.15:
            row["WRITE_EXTERNAL_STORAGE"] = 1
        if rng.random() < 0.1:
            row["RECORD_AUDIO"] = 1
        if rng.random() < 0.05:
            row["READ_CONTACTS"] = 1
        row["FOREGROUND_SERVICE"] = int(rng.random() < 0.3)
        row["RECEIVE_BOOT_COMPLETED"] = int(rng.random() < 0.2)
        row["num_permissions"] = int(rng.integers(2, 8))
        row["label"] = 0
        rows.append(row)

    # ── Malware apps ─────────────────────────────────────────────────────────
    for _ in range(half):
        row = {f: 0 for f in FEATURE_NAMES}
        # Malware typically abuses SMS, CALL, CONTACTS, LOCATION
        row["READ_SMS"] = int(rng.random() < 0.85)
        row["SEND_SMS"] = int(rng.random() < 0.80)
        row["RECEIVE_SMS"] = int(rng.random() < 0.75)
        row["READ_CONTACTS"] = int(rng.random() < 0.90)
        row["WRITE_CONTACTS"] = int(rng.random() < 0.70)
        row["READ_CALL_LOG"] = int(rng.random() < 0.80)
        row["PROCESS_OUTGOING_CALLS"] = int(rng.random() < 0.70)
        row["ACCESS_FINE_LOCATION"] = int(rng.random() < 0.85)
        row["ACCESS_COARSE_LOCATION"] = int(rng.random() < 0.80)
        row["CAMERA"] = int(rng.random() < 0.60)
        row["RECORD_AUDIO"] = int(rng.random() < 0.65)
        row["READ_EXTERNAL_STORAGE"] = int(rng.random() < 0.75)
        row["WRITE_EXTERNAL_STORAGE"] = int(rng.random() < 0.70)
        row["INTERNET"] = int(rng.random() < 0.95)
        row["RECEIVE_BOOT_COMPLETED"] = int(rng.random() < 0.80)
        row["ACCESS_NETWORK_STATE"] = int(rng.random() < 0.80)
        row["FOREGROUND_SERVICE"] = int(rng.random() < 0.60)
        row["num_permissions"] = int(rng.integers(8, 18))
        row["label"] = 1
        rows.append(row)

    df = pd.DataFrame(rows).sample(frac=1, random_state=random_state).reset_index(drop=True)
    return df


def train_and_evaluate():
    print("=" * 60)
    print("  SecureDroid — ML Model Training")
    print("=" * 60)

    # 1. Generate dataset
    print("\n[1] Generating synthetic dataset …")
    df = generate_synthetic_dataset(n_samples=2000)
    print(f"    Total samples : {len(df)}")
    print(f"    Benign (0)    : {(df['label'] == 0).sum()}")
    print(f"    Malware (1)   : {(df['label'] == 1).sum()}")

    # Save dataset
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/android_malware_dataset.csv", index=False)
    print("    Dataset saved → data/android_malware_dataset.csv")

    # 2. Split
    X = df[FEATURE_NAMES].values
    y = df["label"].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n[2] Train/Test split: {len(X_train)} / {len(X_test)}")

    results = {}

    # 3. Train Naive Bayes
    print("\n[3] Training Naive Bayes …")
    nb = GaussianNB()
    nb.fit(X_train, y_train)
    nb_pred = nb.predict(X_test)
    nb_acc = accuracy_score(y_test, nb_pred)
    nb_cv = cross_val_score(nb, X, y, cv=5, scoring="accuracy").mean()
    print(f"    Test Accuracy : {nb_acc:.4f}")
    print(f"    CV Accuracy   : {nb_cv:.4f}")
    print(classification_report(y_test, nb_pred, target_names=["Benign", "Malware"]))
    results["naive_bayes"] = {
        "test_accuracy": round(float(nb_acc), 4),
        "cv_accuracy": round(float(nb_cv), 4),
    }

    # 4. Train Random Forest
    print("\n[4] Training Random Forest …")
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    rf_acc = accuracy_score(y_test, rf_pred)
    rf_cv = cross_val_score(rf, X, y, cv=5, scoring="accuracy").mean()
    print(f"    Test Accuracy : {rf_acc:.4f}")
    print(f"    CV Accuracy   : {rf_cv:.4f}")
    print(classification_report(y_test, rf_pred, target_names=["Benign", "Malware"]))
    results["random_forest"] = {
        "test_accuracy": round(float(rf_acc), 4),
        "cv_accuracy": round(float(rf_cv), 4),
    }

    # Feature importances
    importances = dict(zip(FEATURE_NAMES, rf.feature_importances_.tolist()))
    sorted_imp = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    print("\n    Top-5 Feature Importances (Random Forest):")
    for name, imp in sorted_imp[:5]:
        print(f"      {name:<30} {imp:.4f}")

    # 5. Save models
    os.makedirs("models", exist_ok=True)
    joblib.dump(nb, "models/naive_bayes_model.pkl")
    joblib.dump(rf, "models/random_forest_model.pkl")

    metadata = {
        "feature_names": FEATURE_NAMES,
        "dangerous_permissions": DANGEROUS_PERMISSIONS,
        "labels": {"0": "Benign", "1": "Malware"},
        "model_results": results,
        "feature_importances": dict(sorted_imp),
    }
    with open("models/model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("\n[5] Models saved:")
    print("    models/naive_bayes_model.pkl")
    print("    models/random_forest_model.pkl")
    print("    models/model_metadata.json")
    print("\n✅ Training complete!")
    return results


if __name__ == "__main__":
    train_and_evaluate()
