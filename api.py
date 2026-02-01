from __future__ import annotations

from pathlib import Path

import json

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from models import SubscribeRequest, SubscriberStore
from models.auth import verify_api_key, create_access_token
from models.token import SecretKeyRequest, TokenResponse
from main import run_ipo_automation


store = SubscriberStore()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _auth_middleware(request: Request, call_next):
    try:
        await verify_api_key(request)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return await call_next(request)


app.middleware("http")(_auth_middleware)

WEB_DIR = Path(__file__).resolve().parent / "web"
INDEX_HTML = WEB_DIR / "index.html"

app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

scheduler = AsyncIOScheduler()

@app.post("/subscribe")
def subscribe(payload: SubscribeRequest):
    added = store.add(payload.email)
    if added:
        return {"status": "success", "message": "Successfully subscribed"}
    return {"status": "already", "message": "Already subscribed"}


@app.post("/run")
def run_automation():
    subscribers = store.list_all()
    for email in subscribers: 
        run_ipo_automation(email)
    return {"status": "success", "message": "Automation run completed"}


@app.get("/")
def serve_index():
    if not INDEX_HTML.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(INDEX_HTML)


@app.post("/token")
def get_access_token(payload: SecretKeyRequest):
    try:
        token = create_access_token(payload.secret_key)
        return TokenResponse(access_token=token)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def load_trigger_time() -> tuple[int, int] | None:
    config_path = WEB_DIR / "config.json"
    if not config_path.exists():
        return None

    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        trigger_time = data.get("triggerTime")
        if not isinstance(trigger_time, str) or ":" not in trigger_time:
            return None
        hour_str, minute_str = trigger_time.split(":", 1)
        hour = int(hour_str)
        minute = int(minute_str)
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            return None
        return hour, minute
    except Exception:
        return None


def scheduled_run():
    subscribers = store.list_all()
    for email in subscribers:
        run_ipo_automation(email)


