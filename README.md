# Krushak Hithaishi

Offline-first crop-leaf disease detection for Kannada farmers, with explainable
heatmaps, voice advisories, and a GPS-distance shop directory.

Four stages — only the last needs internet:

1. **Offline** TFLite multimodal model → disease + severity
2. **Offline** Grad-CAM (occlusion) heatmap
3. **Offline→online** IndicTrans2 + gTTS → Kannada voice advisory
4. **Online** shop directory query sorted by GPS distance (Haversine)

## Structure

```
krushak-hithaishi/
├── model_training/   # Google Colab: data prep, train, convert, evaluate
├── backend/          # FastAPI on Railway (Docker)
├── mobile/           # React Native + Expo
└── paper/            # LaTeX write-up
```

## Backend (FastAPI)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate
pip install -r requirements.txt
# PostgreSQL required; set DATABASE_URL or use the default localhost value
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Endpoints:
- `GET  /health` — health check
- `POST /detect` — multipart form (`image`, `lat`, `lon`, `crop_stage`, `language`) → disease, severity, heatmap, translated advisory, voice URL
- `POST /shops/nearby` — JSON `{lat, lon, medicine_name?}` → top 3 shops by distance
- `GET  /advisory/protocol/{disease_name}` — treatment protocol
- `GET  /voice/{filename}` — served TTS audio

Place `krushak.tflite`, `disease_labels.txt`, `severity_labels.txt` in `backend/models/`.
If the model is missing, `/detect` returns a clearly-flagged demo result.

Seed sample shops: `python -m db.seed_shops`

## Mobile (Expo)

```bash
cd mobile
npm install
cp .env.example .env   # set EXPO_PUBLIC_API_URL
npx expo start
```

## Model training (Google Colab)

```bash
pip install -r requirements.txt
python data_prep.py      # build dataset.npz from PlantVillage
python train_model.py    # trains and saves model.keras
python convert_tflite.py # INT8 quantized krushak.tflite
python evaluate.py       # accuracy vs image-only baseline
```
