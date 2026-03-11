"""
SecureDroid - Flask Backend API
Provides endpoints for Android malware detection using ML models.

Endpoints:
  POST /api/scan          - Scan an app (permission features → prediction)
  GET  /api/health        - Health check
  POST /api/report/save   - Encrypt & save a scan report
  POST /api/report/load   - Decrypt & load a saved report
  GET  /api/features      - Return feature list for mobile app
"""

import os
import json
import sys
import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path

from flask import Flask, request, jsonify, g
import joblib
import numpy as np

# Adjust path so we can import crypto_module from the same directory
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from crypto_module import (
    encrypt_scan_report, decrypt_scan_report, sha256_hash, AESCipher
)

# ─────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "SecureDroid-Secret-2024!")
app.config["JWT_SECRET"]  = os.environ.get("JWT_SECRET",  "SecureDroid-JWT-2024!")

# ─────────────────────────────────────────────────────────────
# Load ML models
# ─────────────────────────────────────────────────────────────

MODEL_DIR = BASE_DIR.parent / "ml_model" / "models"

def load_models():
    models = {}
    meta = {}
    try:
        models["random_forest"] = joblib.load(MODEL_DIR / "random_forest_model.pkl")
        models["naive_bayes"]   = joblib.load(MODEL_DIR / "naive_bayes_model.pkl")
        with open(MODEL_DIR / "model_metadata.json") as f:
            meta = json.load(f)
        print(f"[SecureDroid] Models loaded from {MODEL_DIR}")
    except FileNotFoundError:
        print("[SecureDroid] WARNING: Model files not found. Run ml_model/train_model.py first.")
    return models, meta


MODELS, MODEL_META = load_models()
FEATURE_NAMES    = MODEL_META.get("feature_names", [])
DANGEROUS_PERMS  = MODEL_META.get("dangerous_permissions", [])

# ─────────────────────────────────────────────────────────────
# Simple JWT helpers (no external library)
# ─────────────────────────────────────────────────────────────

import base64
import hmac


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))


def create_jwt(payload: dict) -> str:
    header  = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body    = _b64url_encode(json.dumps(payload).encode())
    sig_input = f"{header}.{body}".encode()
    sig = hmac.new(app.config["JWT_SECRET"].encode(), sig_input, hashlib.sha256).digest()
    return f"{header}.{body}.{_b64url_encode(sig)}"


def verify_jwt(token: str) -> dict | None:
    try:
        header, body, sig = token.split(".")
        sig_input = f"{header}.{body}".encode()
        expected = hmac.new(
            app.config["JWT_SECRET"].encode(), sig_input, hashlib.sha256
        ).digest()
        if not hmac.compare_digest(_b64url_decode(sig), expected):
            return None
        payload = json.loads(_b64url_decode(body))
        if payload.get("exp", 0) < datetime.now(timezone.utc).timestamp():
            return None
        return payload
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# Auth decorator
# ─────────────────────────────────────────────────────────────

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth.removeprefix("Bearer ").strip()
        payload = verify_jwt(token)
        if payload is None:
            return jsonify({"error": "Invalid or expired token"}), 401
        g.user = payload
        return f(*args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────────────────────
# In-memory report store (replace with SQLite/Firebase in prod)
# ─────────────────────────────────────────────────────────────

REPORT_STORE: dict[str, dict] = {}

# ─────────────────────────────────────────────────────────────
# Risk assessment helper
# ─────────────────────────────────────────────────────────────

def assess_risk(features: dict, prediction: int, probability: float) -> dict:
    dangerous_used = [p for p in DANGEROUS_PERMS if features.get(p, 0) == 1]
    n_dangerous = len(dangerous_used)

    if prediction == 1 and probability >= 0.85:
        level, color = "CRITICAL", "#FF0000"
    elif prediction == 1 and probability >= 0.60:
        level, color = "HIGH", "#FF4500"
    elif prediction == 1:
        level, color = "MEDIUM", "#FFA500"
    elif n_dangerous >= 5:
        level, color = "MEDIUM", "#FFA500"
    else:
        level, color = "LOW", "#00AA00"

    recommendations = []
    if "READ_SMS" in dangerous_used or "SEND_SMS" in dangerous_used:
        recommendations.append("This app accesses SMS — verify it's a messaging app.")
    if "ACCESS_FINE_LOCATION" in dangerous_used:
        recommendations.append("Fine location access detected — check if location is needed.")
    if "READ_CALL_LOG" in dangerous_used:
        recommendations.append("Call log access detected — unusual for most apps.")
    if "RECORD_AUDIO" in dangerous_used:
        recommendations.append("Microphone access detected — verify necessity.")
    if not recommendations:
        recommendations.append("No specific permission concerns detected.")

    return {
        "risk_level": level,
        "risk_color": color,
        "dangerous_permissions_used": dangerous_used,
        "num_dangerous": n_dangerous,
        "recommendations": recommendations,
    }


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "SecureDroid API",
        "models_loaded": list(MODELS.keys()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.route("/api/token", methods=["POST"])
def get_token():
    """
    Issue a demo JWT token.
    In production, validate username/password against a user store.
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username", "demo")
    exp = (datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()
    token = create_jwt({"sub": username, "exp": exp})
    return jsonify({"token": token, "expires_in": 86400})


@app.route("/api/features", methods=["GET"])
def get_features():
    return jsonify({
        "features": FEATURE_NAMES,
        "dangerous_permissions": DANGEROUS_PERMS,
        "description": "Binary flags (0/1) per permission + num_permissions count",
    })


@app.route("/api/scan", methods=["POST"])
def scan():
    """
    Main scan endpoint.

    Request body (JSON):
      {
        "package_name": "com.example.app",
        "app_name": "Example App",
        "model": "random_forest",   // optional, default random_forest
        "features": {
          "READ_SMS": 1,
          "INTERNET": 1,
          ...
        }
      }

    Response:
      {
        "package_name": "...",
        "app_name": "...",
        "prediction": 0 or 1,
        "label": "Benign" or "Malware",
        "malware_probability": 0.XX,
        "risk": { ... },
        "package_hash": "sha256...",
        "scan_id": "uuid",
        "timestamp": "..."
      }
    """
    if not MODELS:
        return jsonify({"error": "Models not loaded. Run train_model.py first."}), 503

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    package_name = data.get("package_name", "unknown.package")
    app_name     = data.get("app_name", "Unknown App")
    model_key    = data.get("model", "random_forest")
    raw_features = data.get("features", {})

    if model_key not in MODELS:
        return jsonify({"error": f"Unknown model '{model_key}'. Choose from: {list(MODELS.keys())}"}), 400

    # Build feature vector
    if not FEATURE_NAMES:
        return jsonify({"error": "Model metadata not loaded"}), 503

    feature_vector = np.array(
        [raw_features.get(f, 0) for f in FEATURE_NAMES], dtype=float
    ).reshape(1, -1)

    model = MODELS[model_key]
    prediction = int(model.predict(feature_vector)[0])
    probabilities = model.predict_proba(feature_vector)[0]
    malware_prob = float(probabilities[1])

    label = "Malware" if prediction == 1 else "Benign"
    risk  = assess_risk(raw_features, prediction, malware_prob)

    result = {
        "scan_id"           : str(uuid.uuid4()),
        "package_name"      : package_name,
        "app_name"          : app_name,
        "model_used"        : model_key,
        "prediction"        : prediction,
        "label"             : label,
        "malware_probability": round(malware_prob * 100, 2),
        "benign_probability" : round(float(probabilities[0]) * 100, 2),
        "risk"              : risk,
        "package_hash"      : sha256_hash(package_name),
        "timestamp"         : datetime.now(timezone.utc).isoformat(),
    }
    return jsonify(result)


@app.route("/api/report/save", methods=["POST"])
def save_report():
    """
    Encrypt and save a scan report.
    Body: { "report": { ...scan result... } }
    """
    data = request.get_json(silent=True)
    if not data or "report" not in data:
        return jsonify({"error": "Field 'report' required"}), 400

    report = data["report"]
    envelope = encrypt_scan_report(report)
    report_id = report.get("scan_id", str(uuid.uuid4()))
    REPORT_STORE[report_id] = envelope

    return jsonify({
        "status": "saved",
        "report_id": report_id,
        "package_hash": envelope["package_hash"],
    })


@app.route("/api/report/load", methods=["POST"])
def load_report():
    """
    Decrypt a saved scan report.
    Body: { "report_id": "..." }
    """
    data = request.get_json(silent=True)
    if not data or "report_id" not in data:
        return jsonify({"error": "Field 'report_id' required"}), 400

    report_id = data["report_id"]
    envelope = REPORT_STORE.get(report_id)
    if envelope is None:
        return jsonify({"error": "Report not found"}), 404

    decrypted = decrypt_scan_report(envelope)
    return jsonify({"report": decrypted})


@app.route("/api/batch_scan", methods=["POST"])
def batch_scan():
    """
    Scan multiple apps in one request.
    Body: { "apps": [ { "package_name": ..., "features": {...} }, ... ] }
    """
    if not MODELS:
        return jsonify({"error": "Models not loaded"}), 503

    data = request.get_json(silent=True)
    if not data or "apps" not in data:
        return jsonify({"error": "Field 'apps' required"}), 400

    apps = data["apps"]
    model_key = data.get("model", "random_forest")
    model = MODELS.get(model_key)
    if model is None:
        return jsonify({"error": f"Unknown model '{model_key}'"}), 400

    results = []
    for app_data in apps[:50]:  # limit 50
        raw_features = app_data.get("features", {})
        feature_vector = np.array(
            [raw_features.get(f, 0) for f in FEATURE_NAMES], dtype=float
        ).reshape(1, -1)

        prediction = int(model.predict(feature_vector)[0])
        probabilities = model.predict_proba(feature_vector)[0]
        malware_prob = float(probabilities[1])
        risk = assess_risk(raw_features, prediction, malware_prob)

        results.append({
            "package_name"       : app_data.get("package_name", "unknown"),
            "app_name"           : app_data.get("app_name", "Unknown"),
            "prediction"         : prediction,
            "label"              : "Malware" if prediction == 1 else "Benign",
            "malware_probability": round(malware_prob * 100, 2),
            "risk_level"         : risk["risk_level"],
        })

    malware_count = sum(1 for r in results if r["prediction"] == 1)
    return jsonify({
        "total_scanned": len(results),
        "malware_count": malware_count,
        "benign_count" : len(results) - malware_count,
        "results"      : results,
    })


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  SecureDroid Flask API  —  http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, host="0.0.0.0", port=5000)
