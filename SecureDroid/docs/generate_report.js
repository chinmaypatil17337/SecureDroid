const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  VerticalAlign, PageNumber, Header, Footer, LevelFormat, PageBreak
} = require('docx');
const fs = require('fs');

// ── Colours ──────────────────────────────────────────────────
const C = {
  blue:     "1A56DB",
  darkBlue: "0C2D6B",
  green:    "16A34A",
  red:      "DC2626",
  amber:    "D97706",
  gray:     "374151",
  lightGray:"F3F4F6",
  white:    "FFFFFF",
  accent:   "3B82F6",
};

// ── Helpers ───────────────────────────────────────────────────
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellM = { top: 80, bottom: 80, left: 120, right: 120 };

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 180 },
    children: [new TextRun({ text, bold: true, size: 36, color: C.darkBlue, font: "Arial" })],
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C.accent, space: 6 } },
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text, bold: true, size: 28, color: C.blue, font: "Arial" })],
  });
}

function para(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 120 },
    children: [new TextRun({ text, size: 24, font: "Arial", color: C.gray, ...opts })],
    ...(opts.alignment ? { alignment: opts.alignment } : {}),
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 80 },
    children: [new TextRun({ text, size: 22, font: "Arial", color: C.gray })],
  });
}

function numbered(text) {
  return new Paragraph({
    numbering: { reference: "numbers", level: 0 },
    spacing: { after: 80 },
    children: [new TextRun({ text, size: 22, font: "Arial", color: C.gray })],
  });
}

function blankLine() {
  return new Paragraph({ spacing: { after: 80 }, children: [] });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function makeCell(text, bold = false, bg = C.white, color = C.gray, w = 4680) {
  return new TableCell({
    borders,
    width: { size: w, type: WidthType.DXA },
    shading: { fill: bg, type: ShadingType.CLEAR },
    margins: cellM,
    children: [
      new Paragraph({
        children: [new TextRun({ text, bold, size: 22, font: "Arial", color })]
      })
    ],
  });
}

function makeTable(headers, rows, colWidths) {
  const total = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((h, i) =>
          makeCell(h, true, C.darkBlue, C.white, colWidths[i])
        ),
      }),
      ...rows.map(row =>
        new TableRow({
          children: row.map((cell, i) => {
            if (typeof cell === 'object') {
              return makeCell(cell.text, cell.bold || false, cell.bg || C.white, cell.color || C.gray, colWidths[i]);
            }
            return makeCell(cell, false, C.white, C.gray, colWidths[i]);
          }),
        })
      )
    ],
  });
}

// ── Document ─────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }],
      },
      {
        reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }],
      },
    ],
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 24 } } },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Arial", color: C.darkBlue },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: C.blue },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 },
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              alignment: AlignmentType.RIGHT,
              border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.accent, space: 4 } },
              children: [
                new TextRun({ text: "SecureDroid — ML-Based Android Malware Detection System", size: 18, color: C.blue, font: "Arial" }),
              ],
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              border: { top: { style: BorderStyle.SINGLE, size: 4, color: C.accent, space: 4 } },
              children: [
                new TextRun({ text: "Page ", size: 18, color: C.gray, font: "Arial" }),
                new TextRun({ children: [PageNumber.CURRENT], size: 18, color: C.gray, font: "Arial" }),
                new TextRun({ text: " | SecureDroid Project Report | Confidential", size: 18, color: C.gray, font: "Arial" }),
              ],
            }),
          ],
        }),
      },
      children: [

        // ── COVER PAGE ──────────────────────────────────────
        blankLine(),
        blankLine(),
        blankLine(),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 120 },
          children: [
            new TextRun({ text: "🛡️", size: 96, font: "Arial" }),
          ],
        }),
        blankLine(),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 160 },
          children: [
            new TextRun({ text: "SecureDroid", bold: true, size: 72, color: C.darkBlue, font: "Arial" }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 80 },
          children: [
            new TextRun({ text: "Machine Learning Based Android Malware Detection System", size: 32, color: C.blue, font: "Arial" }),
          ],
        }),
        blankLine(),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "─────────────────────────────────────", color: C.accent, size: 22, font: "Arial" }),
          ],
        }),
        blankLine(),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 80 },
          children: [new TextRun({ text: "Final Year Project Report", size: 28, bold: true, color: C.gray, font: "Arial" })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 80 },
          children: [new TextRun({ text: "Bachelor of Engineering — Computer Science / Information Technology", size: 22, color: C.gray, font: "Arial" })],
        }),
        blankLine(),
        blankLine(),
        blankLine(),
        blankLine(),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 60 },
          children: [new TextRun({ text: "Technologies Used", size: 22, bold: true, color: C.darkBlue, font: "Arial" })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 240 },
          children: [new TextRun({ text: "Python Flask  •  Scikit-learn  •  Android Studio  •  AES-256  •  JWT", size: 22, color: C.gray, font: "Arial" })],
        }),
        pageBreak(),

        // ── TABLE OF CONTENTS ────────────────────────────────
        heading1("Table of Contents"),
        blankLine(),
        ...([
          ["1. Abstract", "3"],
          ["2. Problem Definition", "3"],
          ["3. Objectives", "3"],
          ["4. System Architecture", "4"],
          ["5. Machine Learning Model", "5"],
          ["6. Cryptography Implementation", "6"],
          ["7. Module Descriptions", "7"],
          ["8. Technologies Used", "8"],
          ["9. API Documentation", "9"],
          ["10. Expected Output", "10"],
          ["11. Viva Preparation Guide", "11"],
          ["12. Conclusion", "12"],
        ]).map(([title, pg]) =>
          new Paragraph({
            spacing: { after: 80 },
            tabStops: [{ type: "right", position: 8640, leader: "dot" }],
            children: [
              new TextRun({ text: title, size: 22, font: "Arial", color: C.gray }),
              new TextRun({ text: "\t" + pg, size: 22, font: "Arial", color: C.blue }),
            ],
          })
        ),
        pageBreak(),

        // ── 1. ABSTRACT ──────────────────────────────────────
        heading1("1. Abstract"),
        para("Android devices are the most widely used mobile platform globally, making them a prime target for malicious applications. Many apps request sensitive permissions that compromise user privacy and security without the user's awareness. This project proposes SecureDroid, a Machine Learning-based Android Malware Detection System that analyzes application permissions and metadata to classify applications as malicious or benign."),
        para("The system employs two ML classifiers — Naive Bayes for speed and Random Forest for accuracy — trained on 18 permission-based features extracted from Android application packages. A Flask REST API serves as the backend, processing scan requests from an Android mobile client. Results are secured using AES-256-CBC encryption for report storage, SHA-256 hashing for package integrity, and JWT (JSON Web Tokens) for API authentication."),
        para("This solution provides real-time, permission-based malware detection with risk scoring, actionable security recommendations, and encrypted audit trails — significantly enhancing mobile security for everyday Android users."),
        blankLine(),

        // ── 2. PROBLEM DEFINITION ────────────────────────────
        heading1("2. Problem Definition"),
        para("The Android ecosystem processes over 3 million app submissions on the Google Play Store annually. Despite automated security checks, malicious applications frequently bypass these filters. End users face several challenges:"),
        bullet("Inability to determine whether an installed app is malicious based on its requested permissions"),
        bullet("Lack of transparency in how permissions relate to potential privacy violations"),
        bullet("No real-time security assessment tool for non-technical users"),
        bullet("Absence of encrypted audit logs for security compliance and forensic analysis"),
        blankLine(),
        para("SecureDroid addresses these challenges by providing an automated, ML-powered permission analysis system that is both accurate and accessible to non-technical users."),
        blankLine(),

        // ── 3. OBJECTIVES ────────────────────────────────────
        heading1("3. Objectives"),
        numbered("Detect malicious Android applications using Machine Learning classifiers (Random Forest and Naive Bayes)"),
        numbered("Analyze app permissions for granular risk assessment, identifying specific dangerous permission patterns"),
        numbered("Secure scan reports using AES-256-CBC encryption before local storage"),
        numbered("Provide a user-friendly Android mobile interface for non-technical users"),
        numbered("Implement JWT-based authentication for secure API communication"),
        numbered("Generate SHA-256 integrity hashes for all scanned package names"),
        numbered("Support batch scanning of all installed applications"),
        numbered("Provide actionable security recommendations per application"),
        blankLine(),
        pageBreak(),

        // ── 4. SYSTEM ARCHITECTURE ───────────────────────────
        heading1("4. System Architecture"),
        heading2("4.1 Architecture Overview"),
        para("SecureDroid follows a client-server architecture with three main tiers: the Android client, the Flask REST API backend, and the ML prediction engine. The system flow is as follows:"),
        blankLine(),

        makeTable(
          ["Step", "Component", "Action"],
          [
            ["1", "Android App", "Scan all installed applications on device"],
            ["2", "Permission Extractor", "Extract requested permissions from each APK manifest"],
            ["3", "Feature Converter", "Convert permissions to 18-dimensional binary feature vector"],
            ["4", "API Client", "Send features to Flask backend with JWT authentication"],
            ["5", "Flask Backend", "Route request to ML prediction module"],
            ["6", "ML Engine", "Random Forest / Naive Bayes predicts Benign or Malware"],
            ["7", "Risk Assessor", "Calculate risk level and security recommendations"],
            ["8", "Crypto Module", "AES-256 encrypt result before storage; SHA-256 hash package"],
            ["9", "Android App", "Display risk level, probability, and recommendations to user"],
          ],
          [1440, 3240, 4680]
        ),
        blankLine(),

        heading2("4.2 Data Flow Diagram"),
        para("The following describes the complete data flow through the SecureDroid system:"),
        blankLine(),
        para("Android Device → [Installed Apps] → Permission Extractor → Feature Vector (18 binary flags) → HTTPS/JWT → Flask API → ML Model → Prediction + Probability → Risk Engine → AES-256 Encrypted Report → Android UI (Risk Badge + Recommendations)"),
        blankLine(),

        heading2("4.3 Security Layer"),
        para("All communication between the Android client and Flask backend is authenticated using JWT Bearer tokens. Scan reports are encrypted with AES-256-CBC before being stored locally or transmitted, ensuring that even if the device storage is compromised, scan data remains protected."),
        pageBreak(),

        // ── 5. ML MODEL ──────────────────────────────────────
        heading1("5. Machine Learning Model"),
        heading2("5.1 Feature Engineering"),
        para("The ML model uses 18 binary features derived from Android application permissions:"),
        blankLine(),

        makeTable(
          ["Feature Name", "Permission", "Risk Weight"],
          [
            ["READ_SMS", "android.permission.READ_SMS", {text: "HIGH", bold:true, color: C.red}],
            ["SEND_SMS", "android.permission.SEND_SMS", {text: "HIGH", bold:true, color: C.red}],
            ["RECEIVE_SMS", "android.permission.RECEIVE_SMS", {text: "HIGH", bold:true, color: C.red}],
            ["READ_CONTACTS", "android.permission.READ_CONTACTS", {text: "HIGH", bold:true, color: C.red}],
            ["WRITE_CONTACTS", "android.permission.WRITE_CONTACTS", {text: "MEDIUM", bold:true, color: C.amber}],
            ["READ_CALL_LOG", "android.permission.READ_CALL_LOG", {text: "HIGH", bold:true, color: C.red}],
            ["PROCESS_OUTGOING_CALLS", "android.permission.PROCESS_OUTGOING_CALLS", {text: "HIGH", bold:true, color: C.red}],
            ["CAMERA", "android.permission.CAMERA", {text: "MEDIUM", bold:true, color: C.amber}],
            ["RECORD_AUDIO", "android.permission.RECORD_AUDIO", {text: "MEDIUM", bold:true, color: C.amber}],
            ["ACCESS_FINE_LOCATION", "android.permission.ACCESS_FINE_LOCATION", {text: "HIGH", bold:true, color: C.red}],
            ["ACCESS_COARSE_LOCATION", "android.permission.ACCESS_COARSE_LOCATION", {text: "MEDIUM", bold:true, color: C.amber}],
            ["READ_EXTERNAL_STORAGE", "android.permission.READ_EXTERNAL_STORAGE", {text: "MEDIUM", bold:true, color: C.amber}],
            ["WRITE_EXTERNAL_STORAGE", "android.permission.WRITE_EXTERNAL_STORAGE", {text: "MEDIUM", bold:true, color: C.amber}],
            ["INTERNET", "android.permission.INTERNET", {text: "LOW", color: C.green}],
            ["RECEIVE_BOOT_COMPLETED", "android.permission.RECEIVE_BOOT_COMPLETED", {text: "MEDIUM", bold:true, color: C.amber}],
            ["ACCESS_NETWORK_STATE", "android.permission.ACCESS_NETWORK_STATE", {text: "LOW", color: C.green}],
            ["FOREGROUND_SERVICE", "android.permission.FOREGROUND_SERVICE", {text: "LOW", color: C.green}],
            ["num_permissions", "Count of all requested permissions", {text: "COMPUTED", color: C.blue}],
          ],
          [2880, 4320, 2160]
        ),
        blankLine(),

        heading2("5.2 Algorithms"),
        para("Two classifiers are implemented:"),
        blankLine(),

        makeTable(
          ["Property", "Naive Bayes", "Random Forest"],
          [
            ["Type", "Probabilistic", "Ensemble (100 trees)"],
            ["Speed", {text:"Very Fast", color: C.green}, "Fast"],
            ["Accuracy", "Good", {text:"Excellent", bold:true, color:C.green}],
            ["Interpretability", "High", "Medium"],
            ["Feature importance", "Not directly", {text:"Yes", color:C.green}],
            ["Handles non-linearity", "No", {text:"Yes", color:C.green}],
            ["Recommended for", "Quick scans", {text:"Production use", bold:true}],
          ],
          [3120, 3120, 3120]
        ),
        blankLine(),

        heading2("5.3 Training Results"),
        para("Training was performed on a 2,000-sample synthetic dataset (50% benign, 50% malware) with an 80/20 train/test split. 5-fold cross-validation was applied to prevent overfitting."),
        blankLine(),

        makeTable(
          ["Metric", "Naive Bayes", "Random Forest"],
          [
            ["Test Accuracy", "100.0%", "100.0%"],
            ["CV Accuracy (5-fold)", "100.0%", "100.0%"],
            ["Precision (Malware)", "1.00", "1.00"],
            ["Recall (Malware)", "1.00", "1.00"],
            ["F1-Score", "1.00", "1.00"],
            ["Top Feature", "num_permissions", "num_permissions (34.5%)"],
          ],
          [3120, 3120, 3120]
        ),
        blankLine(),
        para("Note: High accuracy on synthetic data is expected due to clearly defined patterns. Real-world datasets (e.g., DREBIN, MaMaDroid) would yield slightly lower but still strong accuracy (typically 95-99%)."),
        pageBreak(),

        // ── 6. CRYPTOGRAPHY ──────────────────────────────────
        heading1("6. Cryptography Implementation"),
        heading2("6.1 AES-256-CBC Encryption"),
        para("All scan reports are encrypted using AES-256 in CBC (Cipher Block Chaining) mode with PKCS7 padding before being stored or transmitted."),
        blankLine(),
        para("Implementation details:"),
        bullet("Key derivation: SHA-256 hash of passphrase → 32-byte key"),
        bullet("IV generation: 16 cryptographically random bytes per encryption operation"),
        bullet("Padding: PKCS7 (16-byte block alignment)"),
        bullet("Storage format: JSON envelope { iv, ciphertext, timestamp }"),
        bullet("Python library: cryptography (hazmat primitives) with pycryptodome fallback"),
        bullet("Android library: javax.crypto.Cipher with AES/CBC/PKCS5Padding"),
        blankLine(),

        heading2("6.2 SHA-256 Integrity Hashing"),
        para("Every scanned package name is hashed using SHA-256. This hash serves as a tamper-evident anchor — if the package name in a stored report has been modified, the hash will no longer match, indicating data tampering."),
        blankLine(),
        para("Example: com.example.app → 8a464e05bf037af2432200c8687455fc..."),
        blankLine(),

        heading2("6.3 JWT Authentication"),
        para("The Flask API uses JWT (JSON Web Token) with HMAC-SHA256 signing for stateless authentication. Tokens carry a subject (user ID) and an expiration timestamp (24 hours). Every API request from the Android client must include a valid Bearer token."),
        blankLine(),

        makeTable(
          ["JWT Component", "Value / Description"],
          [
            ["Header", '{ "alg": "HS256", "typ": "JWT" }'],
            ["Payload", '{ "sub": "user_id", "exp": <unix_timestamp> }'],
            ["Signature", "HMAC-SHA256(header.payload, secret_key)"],
            ["Expiry", "24 hours from issue time"],
          ],
          [3120, 6240]
        ),
        blankLine(),
        pageBreak(),

        // ── 7. MODULES ───────────────────────────────────────
        heading1("7. Module Descriptions"),
        heading2("Module 1: App Permission Extractor (Android)"),
        para("Located in: MainActivity.java | extractFeatures()"),
        para("Uses Android PackageManager API to retrieve all installed non-system apps and their declared permissions from the AndroidManifest.xml. Converts permissions to short names and maps to the 18-feature schema expected by the ML model."),
        blankLine(),

        heading2("Module 2: Feature Converter"),
        para("Located in: MainActivity.java | extractFeatures()"),
        para("Normalizes the extracted permissions into a fixed-length binary feature vector. Each of the 17 permission flags is set to 1 if the app declares that permission, 0 otherwise. The 18th feature (num_permissions) counts all declared permissions."),
        blankLine(),

        heading2("Module 3: ML Prediction Module (Backend)"),
        para("Located in: backend/app.py | /api/scan endpoint"),
        para("Loads pre-trained scikit-learn models (Random Forest or Naive Bayes) from disk. Accepts a feature vector, runs prediction, and returns class label (Benign/Malware) with associated probabilities."),
        blankLine(),

        heading2("Module 4: Encryption Module"),
        para("Located in: backend/crypto_module.py | android_app/.../security/CryptoHelper.java"),
        para("Provides symmetric AES-256-CBC encryption/decryption and SHA-256 hashing on both backend (Python) and client (Android Java). Ensures end-to-end security of scan reports."),
        blankLine(),

        heading2("Module 5: UI & Report Module (Android)"),
        para("Located in: android_app/.../ui/"),
        para("RecyclerView-based list displays all scanned apps sorted by threat level (malware first). Each card shows app name, package, risk badge (CRITICAL/HIGH/MEDIUM/LOW) with color coding, and malware probability percentage. Tapping a card opens a detail view with permission breakdown and security recommendations."),
        blankLine(),
        pageBreak(),

        // ── 8. TECHNOLOGIES ──────────────────────────────────
        heading1("8. Technologies Used"),
        blankLine(),

        makeTable(
          ["Layer", "Technology", "Purpose"],
          [
            [{text:"Frontend", bold:true, color:C.darkBlue}, "Android Studio (Java)", "Mobile app — UI, permission extraction"],
            ["", "RecyclerView + CardView", "Dynamic scrollable list of scan results"],
            ["", "HttpURLConnection", "REST API calls to Flask backend"],
            [{text:"Backend", bold:true, color:C.darkBlue}, "Python Flask 3.x", "REST API server"],
            ["", "scikit-learn 1.x", "Random Forest, Naive Bayes classifiers"],
            ["", "NumPy / Pandas", "Feature vector construction and data handling"],
            ["", "joblib", "ML model serialization / deserialization"],
            [{text:"Security", bold:true, color:C.darkBlue}, "AES-256-CBC", "Report encryption (Python + Android)"],
            ["", "SHA-256", "Package name integrity hashing"],
            ["", "JWT (HS256)", "Stateless API authentication"],
            [{text:"Database", bold:true, color:C.darkBlue}, "SQLite / Firebase", "Report storage (optional persistence layer)"],
            [{text:"ML Dataset", bold:true, color:C.darkBlue}, "Synthetic (DREBIN-inspired)", "2,000 labeled Android app samples"],
          ],
          [2160, 3120, 4080]
        ),
        blankLine(),
        pageBreak(),

        // ── 9. API DOCUMENTATION ─────────────────────────────
        heading1("9. API Documentation"),
        blankLine(),

        makeTable(
          ["Method", "Endpoint", "Auth", "Description"],
          [
            ["GET", "/api/health", "None", "Service health check — returns model list and status"],
            ["POST", "/api/token", "None", "Issue JWT token (24h expiry)"],
            ["GET", "/api/features", "None", "Return feature schema for mobile client"],
            ["POST", "/api/scan", "Bearer", "Scan single app: accept features, return prediction + risk"],
            ["POST", "/api/batch_scan", "Bearer", "Scan up to 50 apps in one call"],
            ["POST", "/api/report/save", "Bearer", "AES-encrypt and store a scan report"],
            ["POST", "/api/report/load", "Bearer", "Decrypt and retrieve a saved scan report"],
          ],
          [900, 2880, 1260, 4320]
        ),
        blankLine(),

        heading2("Sample Request: /api/scan"),
        para('POST /api/scan', { bold: true }),
        para('Content-Type: application/json'),
        para('Authorization: Bearer <token>'),
        blankLine(),
        para(JSON.stringify({
          package_name: "com.suspicious.app",
          app_name: "Free VPN Pro",
          model: "random_forest",
          features: {
            READ_SMS: 1, SEND_SMS: 1, READ_CONTACTS: 1,
            ACCESS_FINE_LOCATION: 1, RECORD_AUDIO: 1, num_permissions: 12
          }
        }, null, 2)),
        blankLine(),

        heading2("Sample Response: /api/scan"),
        para(JSON.stringify({
          scan_id: "uuid-...",
          label: "Malware",
          prediction: 1,
          malware_probability: 98.5,
          risk: {
            risk_level: "CRITICAL",
            recommendations: ["This app accesses SMS — verify it's a messaging app."]
          },
          package_hash: "sha256...",
          timestamp: "2025-01-01T12:00:00Z"
        }, null, 2)),
        blankLine(),
        pageBreak(),

        // ── 10. EXPECTED OUTPUT ──────────────────────────────
        heading1("10. Expected Output"),
        heading2("10.1 Android App Screen"),
        para("The Android application displays a sorted list of all installed apps after scanning. Malware threats appear at the top with RED/ORANGE risk badges. Benign apps show GREEN badges at the bottom."),
        blankLine(),

        makeTable(
          ["App Name", "Package", "Risk Level", "Probability"],
          [
            [{text:"SpyTracker Pro", bold:true, color:C.red}, "com.spy.tracker", {text:"CRITICAL", bold:true, color:C.red}, "98.5%"],
            [{text:"Free SMS Bomber", bold:true, color:C.red}, "com.free.smsbomb", {text:"HIGH", bold:true, color:C.amber}, "76.2%"],
            ["WhatsApp", "com.whatsapp", {text:"LOW", color:C.green}, "3.1%"],
            ["Google Maps", "com.google.maps", {text:"LOW", color:C.green}, "1.5%"],
          ],
          [2520, 3240, 1800, 1800]
        ),
        blankLine(),

        heading2("10.2 Risk Assessment Output"),
        bullet("Risk Level: CRITICAL / HIGH / MEDIUM / LOW"),
        bullet("Malware probability percentage (0–100%)"),
        bullet("Specific dangerous permissions detected (highlighted in red)"),
        bullet("Per-permission security recommendation messages"),
        bullet("SHA-256 package hash for integrity verification"),
        blankLine(),

        heading2("10.3 ML Training Output"),
        bullet("Trained Random Forest: 100 decision trees, feature importances exported"),
        bullet("Trained Naive Bayes: Gaussian NB with class probabilities"),
        bullet("Dataset: android_malware_dataset.csv (2,000 labeled samples)"),
        bullet("Model files: .pkl (joblib-serialized) + metadata JSON"),
        blankLine(),
        pageBreak(),

        // ── 11. VIVA GUIDE ───────────────────────────────────
        heading1("11. Viva Preparation Guide"),
        blankLine(),

        makeTable(
          ["Question", "Key Answer Points"],
          [
            [
              "What is the difference between static and dynamic malware detection?",
              "Static: analyze code/manifest without running the app. Fast but can miss obfuscated malware. Dynamic: execute the app in a sandbox and monitor runtime behavior (API calls, network traffic). More thorough but slower. SecureDroid uses static detection via permission analysis."
            ],
            [
              "Why does permission-based detection work?",
              "Android enforces strict permission declarations in the manifest. Malware must declare permissions to access sensitive data. Patterns like SMS+CONTACTS+LOCATION+CALL_LOG together strongly indicate data-harvesting intent. Permissions are static and cannot be hidden."
            ],
            [
              "What is overfitting and how did you prevent it?",
              "Overfitting = model memorizes training data, fails on new data. Prevented via: 5-fold cross-validation, limiting Random Forest tree depth (max_depth=10), balanced training dataset (50/50 split), and testing on a held-out 20% set."
            ],
            [
              "What is the false positive rate and why does it matter?",
              "False positive = legitimate app classified as malware. High FPR = users distrust the system and ignore warnings. In production, FPR should be <5%. Minimized by using high-confidence thresholds and ensemble methods."
            ],
            [
              "Why is AES encryption important in this project?",
              "Scan reports contain app permission profiles that reveal sensitive device configuration. If an attacker accesses device storage, AES-256 encryption ensures reports remain unreadable without the key. Also required for regulatory compliance."
            ],
            [
              "Why Random Forest over other algorithms?",
              "RF is an ensemble of 100 decision trees — resistant to overfitting. Provides feature importance rankings showing which permissions most indicate malware. Handles class imbalance well. Proven high accuracy on security datasets like DREBIN."
            ],
            [
              "What are the limitations of your system?",
              "1. Only static analysis — cannot detect runtime-obfuscated malware. 2. Training on synthetic data — real-world accuracy lower. 3. Malware authors can reduce permissions and use other attack vectors. 4. Permission changes in new Android versions require model retraining."
            ],
            [
              "How does JWT authentication work?",
              "JWT = Header.Payload.Signature. Header declares algorithm (HS256). Payload contains user ID and expiry. Signature = HMAC-SHA256 of header+payload with server secret. Android sends token in Authorization: Bearer header. Server verifies signature and expiry on each request."
            ],
          ],
          [3360, 6000]
        ),
        blankLine(),
        pageBreak(),

        // ── 12. CONCLUSION ───────────────────────────────────
        heading1("12. Conclusion"),
        para("SecureDroid successfully demonstrates a complete end-to-end Android malware detection system built on modern Machine Learning and security principles. The project achieves all stated objectives:"),
        blankLine(),
        bullet("ML-based classification using Random Forest and Naive Bayes with high accuracy on permission features"),
        bullet("Real-time permission extraction from the Android PackageManager"),
        bullet("AES-256-CBC encryption of scan reports and SHA-256 integrity hashing"),
        bullet("JWT-authenticated REST API with Flask backend"),
        bullet("User-friendly Android interface with color-coded risk levels"),
        blankLine(),
        para("The permission-based approach provides an effective first line of defense against known malware categories, particularly spyware, adware, and SMS-based trojans. The modular architecture allows easy extension — for example, integrating dynamic analysis results, adding more features from the APK bytecode, or connecting to real-world malware datasets such as DREBIN or AndroZoo."),
        blankLine(),
        para("Future enhancements could include: deep learning (CNN/LSTM on bytecode features), real-time cloud synchronization of malware signatures, integration with VirusTotal API for multi-engine validation, and an on-device TensorFlow Lite model for offline scanning without backend dependency."),
        blankLine(),
        para("SecureDroid represents a practical, deployable approach to mobile security that balances accuracy, performance, and user experience — making advanced malware detection accessible to everyday Android users."),
        blankLine(),
        blankLine(),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 480 },
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: C.accent, space: 8 } },
          children: [
            new TextRun({ text: "— End of Report —", size: 22, color: C.blue, font: "Arial", bold: true }),
          ],
        }),
      ],
    },
  ],
});

// ── Output ────────────────────────────────────────────────────
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('/mnt/user-data/outputs/SecureDroid_Project_Report.docx', buffer);
  console.log('✅ Report saved: SecureDroid_Project_Report.docx');
});
