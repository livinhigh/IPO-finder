from __future__ import annotations

from pathlib import Path

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from models import SubscribeRequest, SubscriberStore
from main import run_ipo_automation


store = SubscriberStore()


@asynccontextmanager
async def lifespan(_: FastAPI):
    trigger_time = load_trigger_time()
    if trigger_time:
        hour, minute = trigger_time
        scheduler.add_job(scheduled_run, CronTrigger(hour=hour, minute=minute))
        scheduler.start()
    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown()


#app = FastAPI(lifespan=lifespan)
app = FastAPI()

WEB_DIR = Path(__file__).resolve().parent / "web"
INDEX_HTML = WEB_DIR / "index.html"

app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = AsyncIOScheduler()

@app.post("/subscribe")
def subscribe(payload: SubscribeRequest):
    try:
        added = store.add(payload.email)
        if added:
            return {"status": "success", "message": "Successfully subscribed"}
        return {"status": "already", "message": "Already subscribed"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/run")
def run_automation():
    try:
        subscribers = store.list_all()
        errors = []

        for email in subscribers:
            try:
                run_ipo_automation(email)
            except Exception as exc:
                errors.append({"email": email, "error": str(exc)})

        if errors:
            return {"status": "error", "message": "Some runs failed", "errors": errors}

        return {"status": "success", "message": "Run completed", "processed": len(subscribers)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/")
def serve_index():
    if not INDEX_HTML.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(INDEX_HTML)


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


