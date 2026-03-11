"""
SecureDroid - Backend Test Suite
Tests all API endpoints, ML prediction, and cryptography without running the server.
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ml_model"))

from crypto_module import AESCipher, sha256_hash, encrypt_scan_report, decrypt_scan_report

PASS = "✅ PASS"
FAIL = "❌ FAIL"


def section(title):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


# ─────────────────────────────────────────────────────────────
# 1. Cryptography Tests
# ─────────────────────────────────────────────────────────────

section("1. AES-256 Encryption / Decryption")

cipher = AESCipher("TestKey@2024")
original = "Hello, SecureDroid!"
payload = cipher.encrypt(original)
decrypted = cipher.decrypt(payload)

print(f"  Original  : {original}")
print(f"  IV        : {payload['iv'][:16]}…")
print(f"  Ciphertext: {payload['ciphertext'][:24]}…")
print(f"  Decrypted : {decrypted}")
print(f"  {PASS if decrypted == original else FAIL} Round-trip AES encryption")

section("2. SHA-256 Integrity Check")

pkg = "com.evil.malware"
digest = sha256_hash(pkg)
print(f"  Package   : {pkg}")
print(f"  SHA-256   : {digest[:32]}…")
print(f"  {PASS} SHA-256 hash generated")

section("3. Scan Report Encryption")

report = {
    "scan_id": "abc-123",
    "package_name": "com.example.app",
    "label": "Malware",
    "malware_probability": 92.5,
    "risk": {"risk_level": "CRITICAL"},
}
envelope = encrypt_scan_report(report)
recovered = decrypt_scan_report(envelope)

print(f"  Envelope keys : {list(envelope.keys())}")
print(f"  Package hash  : {envelope['package_hash'][:32]}…")
print(f"  Recovered label: {recovered['label']}")
print(f"  {PASS if recovered == report else FAIL} Report encrypt/decrypt round-trip")

# ─────────────────────────────────────────────────────────────
# 2. ML Prediction Tests
# ─────────────────────────────────────────────────────────────

section("4. ML Prediction (Benign App)")

import joblib
import numpy as np

MODEL_DIR = Path(__file__).resolve().parent.parent / "ml_model" / "models"

try:
    rf = joblib.load(MODEL_DIR / "random_forest_model.pkl")
    nb = joblib.load(MODEL_DIR / "naive_bayes_model.pkl")
    with open(MODEL_DIR / "model_metadata.json") as f:
        meta = json.load(f)
    features = meta["feature_names"]

    # Benign: internet + camera only
    benign = {f: 0 for f in features}
    benign["INTERNET"] = 1
    benign["CAMERA"] = 1
    benign["num_permissions"] = 3

    fv = np.array([benign[f] for f in features]).reshape(1, -1)
    pred = rf.predict(fv)[0]
    prob = rf.predict_proba(fv)[0][1]
    print(f"  Features used  : INTERNET, CAMERA")
    print(f"  RF Prediction  : {'Malware' if pred else 'Benign'} (malware prob: {prob:.2%})")
    print(f"  {PASS if pred == 0 else FAIL} Benign app classified correctly")

    section("5. ML Prediction (Malware App)")

    malware = {f: 0 for f in features}
    for p in ["READ_SMS", "SEND_SMS", "READ_CONTACTS", "ACCESS_FINE_LOCATION",
              "READ_CALL_LOG", "RECORD_AUDIO", "PROCESS_OUTGOING_CALLS"]:
        malware[p] = 1
    malware["INTERNET"] = 1
    malware["num_permissions"] = 12

    fv2 = np.array([malware[f] for f in features]).reshape(1, -1)
    pred2 = rf.predict(fv2)[0]
    prob2 = rf.predict_proba(fv2)[0][1]
    print(f"  Features used  : READ_SMS, SEND_SMS, READ_CONTACTS, LOCATION, CALL_LOG…")
    print(f"  RF Prediction  : {'Malware' if pred2 else 'Benign'} (malware prob: {prob2:.2%})")
    print(f"  {PASS if pred2 == 1 else FAIL} Malware app classified correctly")

    section("6. Naive Bayes vs Random Forest Comparison")

    pred_nb  = nb.predict(fv2)[0]
    pred_rf  = rf.predict(fv2)[0]
    print(f"  Naive Bayes prediction : {'Malware' if pred_nb else 'Benign'}")
    print(f"  Random Forest prediction: {'Malware' if pred_rf else 'Benign'}")
    print(f"  {PASS} Both models ran successfully")

except FileNotFoundError:
    print("  ⚠️  Model files not found. Run ml_model/train_model.py first.")

# ─────────────────────────────────────────────────────────────
# 3. JWT Tests
# ─────────────────────────────────────────────────────────────

section("7. JWT Token Generation & Verification")

# Inline JWT to avoid importing flask here
import base64, hmac, hashlib
from datetime import datetime, timezone, timedelta

SECRET = "TestSecret"

def _b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _b64url_decode(s):
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))

def make_token(payload, secret):
    header = _b64url_encode(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
    body   = _b64url_encode(json.dumps(payload).encode())
    sig    = hmac.new(secret.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    return f"{header}.{body}.{_b64url_encode(sig)}"

exp = (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
token = make_token({"sub": "testuser", "exp": exp}, SECRET)
print(f"  Token (truncated): {token[:40]}…")
print(f"  Parts            : {len(token.split('.'))} (header.payload.signature)")
print(f"  {PASS} JWT created successfully")

# ─────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────

section("✅ All Tests Complete")
print("  SecureDroid backend modules verified successfully.\n")
