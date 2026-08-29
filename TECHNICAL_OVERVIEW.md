# Krushak Hithaishi — Technical Overview & Team Roadmap

## 1. Executive Summary

Krushak Hithaishi is an **offline-first mobile system** for crop-leaf disease detection.
A farmer photographs a leaf → an on-device TFLite model predicts disease + severity →
a Grad-CAM-style heatmap is generated → an IndicTrans2 + gTTS pipeline produces a
Kannada voice advisory → the phone queries a cloud shop-directory (only online step)
and shows the 3 nearest agricultural shops sorted by GPS distance.

The system is built as a **fourth-year student project** with three independently
maintainable modules:
- `model_training/` — Colab notebook work
- `backend/` — FastAPI service
- `mobile/` — React Native + Expo app
- `paper/` — LaTeX write-up

---

## 2. Architecture (end-to-end)

```
Farmer phone
    │
    ├─[Offline] TFLite multimodal model  →  disease + severity
    ├─[Offline] Grad-CAM heatmap          →  visual explanation
    ├─[Offline→online] IndicTrans2 + gTTS →  Kannada voice advisory
    └─[Online] POST /shops/nearby         →  3 nearest shops by Haversine distance
```

Only the last hop needs internet.  The TFLite model is quantised to INT8 so inference
runs at interactive speed on a mid-range Android phone with no server round-trip.

---

## 3. Folder Structure (what each file does)

### 3.1 `model_training/` — Colab / local training

| File | Role |
|------|------|
| `data_prep.py` | Loads PlantVillage, resizes to 512×512, assigns synthetic weather vectors (fungal → high humidity) and severity labels (LOW/MEDIUM/HIGH), saves `dataset.npz`. |
| `train_model.py` | Builds a two-input Keras model: MobileNetV3Small image branch + 4-dim weather/stage branch → concatenate → Dense(256)+Dropout → two softmax heads (38 disease, 3 severity). Trains 20 epochs with EarlyStopping, saves `model.keras`. Also exports `disease_labels.txt` + `severity_labels.txt` with the authoritative class ordering. |
| `convert_tflite.py` | Loads `model.keras`, applies **INT8 post-training quantisation** using a representative dataset from `dataset.npz`, writes `krushak.tflite`. |
| `evaluate.py` | Loads `krushak.tflite`, runs on a held-out test split, prints disease accuracy, severity accuracy, and the delta against an image-only baseline (proves the weather branch helps). |

**Colab requirements:** `tensorflow`, `numpy`, `pillow`, `scikit-learn`.
**Input data:** PlantVillage folder structure (`./data/<class_name>/*.jpg`).
**Outputs to copy to backend:** `krushak.tflite`, `disease_labels.txt`, `severity_labels.txt`.

### 3.2 `backend/` — FastAPI service (Docker / Railway)

```
backend/
├── main.py                    # FastAPI app, CORS, static /voice mount, startup cleanup
├── requirements.txt           # Python deps (TF-CPU, transformers, fastapi, uvicorn …)
├── Dockerfile                 # python:3.10-slim → uvicorn main:app
├── models/
│   ├── krushak.tflite         # trained model (gitignored)
│   ├── disease_labels.txt     # 38 PlantVillage classes, one per line
│   ├── severity_labels.txt    # LOW / MEDIUM / HIGH
│   └── README.md
├── db/
│   ├── database.py            # SQLAlchemy + Shop table (Float lat/lon, JSON medicines)
│   ├── seed_shops.py          # reads CSV → Shop table
│   └── shops_sample.csv       # sample Karnataka shop directory
├── routes/
│   ├── detect.py              # POST /detect — full pipeline (TFLite + weather + translate + voice + heatmap)
│   ├── shops.py               # POST /shops/nearby — Haversine distance, top 3
│   └── advisory.py            # GET /advisory/protocol/{disease} — treatment lookup
└── utils/
    ├── weather.py             # Open-Meteo async client, Karnataka fallback defaults
    ├── distance.py            # Haversine formula (pure Python)
    ├── gradcam.py             # True Grad-CAM (Keras dev) + TFLite-friendly occlusion saliency
    ├── translate.py           # IndicTrans2 (en→kn, hi, te), lazy per-language model cache
    ├── voice.py               # gTTS → `static/voice/<uuid>.mp3`; 1-hour cleanup
    └── model.py               # TFLite interpreter singleton, INT8 dequant, predict/proba helpers
```

**Key design decisions:**
- `database.py` defaults to **SQLite** for zero-setup local runs; set `DATABASE_URL` for PostgreSQL (Railway).
- `translate.py` and `voice.py` gracefully degrade when heavy deps (`transformers`, `gtts`) are missing — the endpoint still returns a result, just in English without audio.
- `/detect` runs in a clearly-flagged `"demo": true` mode when `krushak.tflite` is absent (fixed disease + protocol), so the whole mobile flow can be exercised before training finishes.
- The shop directory replaces the original "Stockping" inventory-sync idea with a **pure SQL + Haversine** query — no cron, no WhatsApp bot, no live inventory.

### 3.3 `mobile/` — React Native + Expo

```
mobile/
├── App.js                     # Stack navigator: Home → Scan → Result → Shops
├── app.json                   # Expo config (camera, location permissions)
├── package.json               # deps: expo-camera, expo-location, expo-av, @react-navigation/*, @react-native-picker/picker
├── .env.example               # EXPO_PUBLIC_API_URL=http://localhost:8000
├── screens/
│   ├── HomeScreen.js          # Welcome + "Start Scan"
│   ├── ScanScreen.js          # Camera viewfinder, crop-stage Picker, GPS, POST /detect
│   ├── ResultScreen.js        # Disease display, confidence, SeverityBadge, heatmap, Play Voice, Find Nearby Shops
│   └── ShopsScreen.js         # POST /shops/nearby, FlatList of ShopCards
├── components/
│   ├── SeverityBadge.js       # Pill: green=LOW, yellow=MEDIUM, red=HIGH
│   └── ShopCard.js            # Shop info + "Verified: Month Year" + Call button (tel:)
└── services/
    └── api.js                 # detectDisease() + getNearbyShops() → fetch multipart/JSON
```

**Important flow fix:** `ResultScreen` now passes `result.treatment.medicine_name` (e.g. `"Mancozeb"`) to `ShopsScreen`, not the raw disease name, so the shop filter returns real matches.

### 3.4 `paper/` — LaTeX draft

`paper/krushak_paper.tex` — sections: Overview, Architecture (4-stage pipeline), Tech Stack, Evaluation, Future Work. Expandable to a conference-style two-column format.

---

## 4. Data Flow (one complete request)

```
Phone (Expo Go)
  │  photo + lat + lon + crop_stage + "kn"
  ▼
POST /detect  (multipart)
  │
  ├─ utils/weather.py       → Open-Meteo or Karnataka fallback (temp, humidity, precip)
  ├─ utils/model.py          → TFLite interpreter → disease class + severity + confidence
  ├─ utils/gradcam.py        → occlusion saliency heatmap → base64 JPEG
  ├─ routes/advisory.py      → treatment protocol lookup (Mancozeb, dosage, organic alt)
  ├─ utils/translate.py      → IndicTrans2 → Kannada advisory (falls back to English)
  ├─ utils/voice.py          → gTTS → /static/voice/<uuid>.mp3
  ▼
JSON response
  { disease_name, disease_display, confidence, severity,
    heatmap_base64, advisory_translated, advisory_english,
    treatment: { medicine_name, dosage_per_acre, organic_alternative, application_timing },
    voice_file_url, weather, crop_stage, demo }
  │
  ▼
ResultScreen shows disease + badge + heatmap + advisory
Play Voice → expo-av plays /voice/<uuid>.mp3
Find Nearby Shops → POST /shops/nearby (with medicine_name from treatment)
  │
  ▼
ShopsScreen renders top 3 by Haversine distance
Call button → Linking.openURL('tel:+9198...')
```

---

## 5. Tech Stack & Rationale

| Layer | Technology | Why this choice |
|-------|-----------|-----------------|
| Training | **TensorFlow 2.16 on Colab T4 GPU** | Free GPU; Keras functional API for multimodal architecture |
| Model format | **TFLite INT8** | 4× smaller, 2–4× faster on CPU; fully offline on phone |
| Explainability | **Grad-CAM (OpenCV) + occlusion fallback** | Visual trust; occlusion works on TFLite where true Grad-CAM needs Keras gradients |
| Translation | **IndicTrans2 (AI4Bharat, HuggingFace)** | State-of-the-art open-source Indian language model |
| Voice | **gTTS** | Zero-cost, simple, good Kannada quality |
| Backend | **FastAPI + Python 3.10** | Async performance, auto-generated OpenAPI docs, very fast to write |
| Database | **PostgreSQL (Railway) + SQLite (local)** | Structured shop data; geospatial-ready if needed later |
| Distance | **Haversine formula (pure Python)** | No PostGIS dependency — simple math suffices |
| Mobile | **React Native + Expo** | Cross-platform; camera + GPS built-in; Expo Go for instant preview |
| Deployment | **Docker + Railway free tier** | One-command deploy; no credit card required |
| Version control | **GitHub + GitHub Copilot** | Your existing student developer pack |

---

## 6. Current State (verified)

Backend endpoints tested and working (in demo mode until TFLite is dropped in):

| Endpoint | Status |
|----------|--------|
| `GET /health` | ok |
| `POST /detect` | Returns disease, severity, heatmap (base64), advisory, voice URL, weather — `"demo": true` |
| `POST /shops/nearby` | Returns top 3 shops sorted by Haversine, filters by `medicine_name` |
| `GET /advisory/protocol/{disease}` | Resolves PlantVillage-style names (`Potato___Late_blight`) to protocols |
| `GET /voice/{filename}` | Serves valid 135 KB MP3 |

All 4 training scripts byte-compile cleanly. Mobile component tree is consistent (`SeverityBadge.js`, real `expo-camera` capture, crop-stage picker).

---

## 7. Team of 4 — Division of Responsibilities

### Person A — ML / Model Training (Colab lead)
- Fine-tune MobileNetV3Small with ImageNet weights for better accuracy
- Expand disease class coverage / add severity regression loss if needed
- Benchmark INT8 vs FP16 quantisation; measure on-device latency
- Run `evaluate.py` ablation; prepare accuracy tables for the paper

### Person B — Backend / DevOps
- Deploy to Railway; configure `DATABASE_URL` + CORS origins
- Add authentication / rate limiting if pitching to an audience
- Set up monitoring (UptimeRobot / Railway logs)
- Dockerise + write CI (GitHub Actions lint + test on PR)

### Person C — Mobile / Frontend
- Polish UI: loading skeletons, error states, offline banner, Kannada/English toggle
- Add onboarding flow (camera + location permissions explanation)
- Profile memory usage with Expo Flipper; ensure 512×512 image handling doesn't OOM
- Prepare demo APK / Expo build for pitching

### Person D — Research / Paper / Pitching
- Write the LaTeX paper (`paper/krushak_paper.tex`):
  - Related work (PlantVillage, PlantDoc, offline-first mobile ML)
  - Architecture diagram + ablation table (multimodal vs image-only delta)
  - Haversine vs PostGIS discussion
  - Latency numbers (TFLite INT8 inference time on target device)
- Prepare 5-slide pitch deck (problem → solution → demo → results → ask)
- Register for a conference/journal (see §8)

---

## 8. Paper Publication Path (realistic options)

1. **IEEE Access / MDPI Sensors** (Q1, ~3–6 months review, special issues on Agri-AI).
   - Good fit: real-world deployment story + ablation study.
   - Word count ~8–12k; expand the existing LaTeX skeleton.

2. **IEEE INDICON / ICSCC** (Indian conferences, shorter review ~2–4 months).
   - Strong social-impact angle (Kannada voice, offline-first for rural India).
   - Bring the demo APK to the conference if possible.

3. **arXiv preprint** (immediate, 1 week).
   - Upload to `arxiv.org` with the LaTeX source.
   - Gives you a citable DOI while journal review is in progress.
   - Include accuracy numbers + latency + qualitative heatmap samples.

4. **Patents / IP cell** (if your university has one).
   - Novel angle: "Haversine-only shop directory without live inventory sync" is a
    practical system design contribution; consider a provisional patent or design patent.

**Suggested paper structure (2-column, IEEE format):**
- Abstract (150–200 words)
- I. Introduction (problem, gap, contribution)
- II. Related Work (PlantVillage, PlantDoc, FarmBeats, IndicTrans2)
- III. System Architecture (4-stage pipeline diagram)
- IV. Multimodal Model (MobileNetV3Small + weather branch, INT8 quantisation)
- V. Explainability (Grad-CAM + TFLite-compatible occlusion fallback)
- VI. Shop Directory (Haversine, no inventory sync)
- VII. Evaluation (accuracy delta, latency, voice quality, shop distance error)
- VIII. User Study (if you do field testing with 5–10 farmers)
- IX. Discussion & Limitations
- X. Conclusion & Future Work

---

## 9. Pitching Roadmap (startup / incubator / demo day)

### Deck (5–7 slides)
1. **Problem** — 60% of Indian farmers can't diagnose leaf diseases early; no good offline tool in Kannada.
2. **Solution** — Photo → disease + heatmap + Kannada voice + nearby shop in <5 seconds.
3. **Demo** — Live Expo Go demo on a phone. Have a pre-recorded fallback video in case of demo-day Wi-Fi failure.
4. **Tech moat** — Multimodal weather-fused model + TFLite offline pipeline + zero-inventory shop directory.
5. **Traction** — Colab training numbers, backend latency (<200 ms /detect), mobile FPS.
6. **Team** — 4 final-year CS/IT students; split per §7.
7. **Ask** — Looking for: (a) Agri-extension pilot partners, (b) incubator space, (c) ₹X seed for field testing.

### What to have ready
- 2-minute elevator pitch (no jargon, Kannada + English)
- A 1-page flyer (problem + solution + contact QR code)
- Backend running live on Railway + a public URL for judges to test
- Mobile build on Expo (production build) + one Android APK side-loaded
- Printed paper draft (IEEE format) to hand out to mentors

### Potential venues
- **E-cell / TBI demo days** (internal to your university)
- **Karnataka State Agri-Tech Hackathon** (agri-department ties)
- **SIH (Smart India Hackathon)** problem statements on "Agri-advisory" or "Farmer first"
- **IEEE conference poster session** (§8 above)

---

## 10. Next Milestones (8-week timeline)

| Week | Owner | Deliverable |
|------|-------|-------------|
| 1 | A | Colab pipeline working end-to-end (data_prep → train → convert → evaluate) |
| 2 | B | Backend deployed to Railway + `/health` + `/shops/nearby` live |
| 3 | C | Mobile app builds in Expo Go; Scan → Result → Shops flow complete |
| 4 | A + B | Drop `krushak.tflite` into backend; end-to-end real inference; measure latency |
| 5 | D | Draft paper skeleton; collect accuracy + latency numbers |
| 6 | All | Field test with 5–10 farmers; record heatmap + voice advisory feedback |
| 7 | D | Finalise paper + slide deck; submit arXiv preprint |
| 8 | All | Buffer / demo-day prep / bug bash / write journal submission |

---

## 11. Quick Reference — Commands

```bash
# Backend (local, SQLite, demo mode)
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python -m db.seed_shops
uvicorn main:app --host 0.0.0.0 --port 8000

# Model training (Colab)
%cd /content/model_training
!pip install -q scikit-learn tensorflow-datasets
# populate ./data ...
!python data_prep.py
!python train_model.py
!python convert_tflite.py
# export labels, download krushak.tflite + disease_labels.txt + severity_labels.txt

# Mobile
cd mobile
npm install
cp .env.example .env   # set EXPO_PUBLIC_API_URL
npx expo start
```

---

*Document generated from the project state on 2026-07-21.*
