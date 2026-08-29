from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes.advisory import router as advisory_router
from routes.detect import router as detect_router
from routes.shops import router as shops_router
from utils.voice import cleanup_old_files

import os

app = FastAPI(title="Krushak Hithaishi", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VOICE_DIR = os.path.join(os.path.dirname(__file__), "static", "voice")
os.makedirs(VOICE_DIR, exist_ok=True)
app.mount("/voice", StaticFiles(directory=VOICE_DIR), name="voice")

app.include_router(detect_router)
app.include_router(advisory_router)
app.include_router(shops_router)


@app.on_event("startup")
def _startup():
    cleanup_old_files()


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "krushak-hithaishi"}
