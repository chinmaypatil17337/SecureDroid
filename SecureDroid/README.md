# 🛡️ SecureDroid — ML-Based Android Malware Detection System

> **Final Year Project** | Machine Learning + Android + Flask + AES Cryptography

---

## 📋 Project Overview

SecureDroid detects malicious Android applications by analyzing their declared permissions using Machine Learning. A trained Random Forest classifier (and optionally Naive Bayes) predicts whether an app is **Benign** or **Malware** based on 18 permission-derived features. Results are encrypted with AES-256 before storage, and communication uses JWT authentication.

---

## 🏗️ Architecture

```
Android App (Java)
     │
     │  POST /api/scan  (features JSON + JWT)
     ▼
Flask REST API  ←──── ML Model (Random Forest / Naive Bayes)
     │                        │
     │                        └── Predict: 0=Benign / 1=Malware
     │
     ├── AES-256-CBC  ──► Encrypt scan report
     ├── SHA-256      ──► Hash package name
     └── JWT (HS256)  ──► Authenticate mobile ↔ backend
```

---

## 📁 Project Structure

```
SecureDroid/
├── ml_model/
│   ├── train_model.py          # Dataset generation + model training
│   ├── data/
│   │   └── android_malware_dataset.csv
│   └── models/
│       ├── random_forest_model.pkl
│       ├── naive_bayes_model.pkl
│       └── model_metadata.json
│
├── backend/
│   ├── app.py                  # Flask API (all endpoints)
│   ├── crypto_module.py        # AES-256, SHA-256 helpers
│   └── requirements.txt
│
├── android_app/
│   └── app/src/main/java/com/securedroid/malwaredetector/
│       ├── MainActivity.java
│       ├── api/ApiClient.java
│       ├── model/AppScanResult.java
│       └── security/CryptoHelper.java
│
├── scripts/
│   └── test_backend.py         # Full test suite (7 tests)
│
└── README.md
```

---

## ⚡ Quick Start

### 1. Train ML Models

```bash
cd ml_model
python3 train_model.py
```

Expected output: Random Forest ~100% accuracy on synthetic data.

### 2. Start Flask Backend

```bash
cd backend
pip install -r requirements.txt
python3 app.py
```

Server starts at: `http://localhost:5000`

### 3. Test the Backend

```bash
# Health check
curl http://localhost:5000/api/health

# Scan a sample app
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "package_name": "com.test.app",
    "app_name": "Test App",
    "features": {
      "READ_SMS": 1,
      "SEND_SMS": 1,
      "READ_CONTACTS": 1,
      "ACCESS_FINE_LOCATION": 1,
      "INTERNET": 1,
      "num_permissions": 10
    }
  }'

# Run automated tests
python3 scripts/test_backend.py
```

### 4. Build Android App

Open `android_app/` in Android Studio → Build → Run.

---

## 🧠 ML Model Details

| Feature | Importance |
|---|---|
| num_permissions | 34.5% |
| READ_SMS | 19.7% |
| READ_CONTACTS | 13.0% |
| READ_CALL_LOG | 9.6% |
| SEND_SMS | 8.7% |

**Algorithm**: Random Forest (100 trees, max_depth=10)  
**Dataset**: 2,000 synthetic samples (1,000 benign, 1,000 malware)  
**Accuracy**: ~100% on synthetic data; real-world depends on dataset quality

---

## 🔐 Security Implementation

| Mechanism | Purpose |
|---|---|
| AES-256-CBC | Encrypt scan reports before local storage |
| SHA-256 | Integrity hash of app package names |
| JWT (HS256) | Authenticate Android ↔ Flask API calls |

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Service health check |
| POST | `/api/token` | Get JWT auth token |
| GET | `/api/features` | Feature list for mobile |
| POST | `/api/scan` | Scan single app |
| POST | `/api/batch_scan` | Scan multiple apps |
| POST | `/api/report/save` | Encrypt & save report |
| POST | `/api/report/load` | Decrypt & load report |

---

## 📊 Risk Levels

| Level | Condition |
|---|---|
| 🔴 CRITICAL | Malware predicted, probability ≥ 85% |
| 🟠 HIGH | Malware predicted, probability ≥ 60% |
| 🟡 MEDIUM | Malware predicted / 5+ dangerous permissions |
| 🟢 LOW | Benign, few dangerous permissions |

---

## 🎤 Viva Q&A Summary

**Static vs Dynamic Detection**: Static analyzes code/permissions without executing the app. Dynamic runs the app in a sandbox and monitors runtime behavior. This project uses static (permission-based) detection.

**Why permission-based**: Android enforces declared permissions — they reveal intent. SMS+CONTACTS+LOCATION together strongly indicate data-harvesting malware.

**Overfitting**: When a model memorizes training data and fails on unseen data. Prevented by cross-validation and limited tree depth.

**False Positive Rate**: Legitimate apps classified as malware. High false positives reduce user trust.

**Why Encryption**: Scan reports may contain sensitive app data. AES-256 ensures they can't be read even if the device storage is accessed.

---

## 👥 Team

| Role | Responsibility |
|---|---|
| ML Engineer | Model training, feature engineering |
| Backend Dev | Flask API, JWT, crypto module |
| Android Dev | Permission extraction, UI, API integration |
| Security Analyst | AES/SHA design, risk assessment logic |
