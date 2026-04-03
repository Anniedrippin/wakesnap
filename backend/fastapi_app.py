import os
import sys
import random
import uuid
import base64
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_VISION_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_VISION_API_KEY not set in environment variables")

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from fastapi import FastAPI, HTTPException, File, UploadFile, Request
from starlette.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from alarm_app.models import Alarm, RoomObjects, AlarmSession

app = FastAPI(
    title="WakeSnap API",
    version="1.0.0",
    description="Alarm app that forces you to photograph an object to dismiss",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global handler: ensures CORS headers are present even on unhandled 500s
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()  # prints to uvicorn log so you can see the real error
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"Access-Control-Allow-Origin": "*"},
    )

MEDIA_DIR = Path(__file__).parent / "media" / "alarm_photos"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


# ── Schemas ────────────────────────────────────────────────────────────────────

class AlarmCreateSchema(BaseModel):
    label: str = "Wake Up!"
    time: str  # HH:MM format
    days: list[int] = []


class TriggerResponse(BaseModel):
    session_id: str
    object_name: str
    object_emoji: str
    hint: str
    category: str


class VerifyResponse(BaseModel):
    success: bool
    message: str
    detected_label: Optional[str] = None
    confidence: Optional[float] = None
    session_id: str


# ── Basic routes ───────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "WakeSnap API running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.get("/test-vision")
def test_vision():
    """Hit this in browser to check if Google Vision API key is working."""
    import urllib.request
    # 1x1 white pixel JPEG
    test_image = bytes([
        0xff,0xd8,0xff,0xe0,0x00,0x10,0x4a,0x46,0x49,0x46,0x00,0x01,0x01,0x00,0x00,0x01,
        0x00,0x01,0x00,0x00,0xff,0xdb,0x00,0x43,0x00,0x08,0x06,0x06,0x07,0x06,0x05,0x08,
        0x07,0x07,0x07,0x09,0x09,0x08,0x0a,0x0c,0x14,0x0d,0x0c,0x0b,0x0b,0x0c,0x19,0x12,
        0x13,0x0f,0x14,0x1d,0x1a,0x1f,0x1e,0x1d,0x1a,0x1c,0x1c,0x20,0x24,0x2e,0x27,0x20,
        0x22,0x2c,0x23,0x1c,0x1c,0x28,0x37,0x29,0x2c,0x30,0x31,0x34,0x34,0x34,0x1f,0x27,
        0x39,0x3d,0x38,0x32,0x3c,0x2e,0x33,0x34,0x32,0xff,0xc0,0x00,0x0b,0x08,0x00,0x01,
        0x00,0x01,0x01,0x01,0x11,0x00,0xff,0xc4,0x00,0x1f,0x00,0x00,0x01,0x05,0x01,0x01,
        0x01,0x01,0x01,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x01,0x02,0x03,0x04,
        0x05,0x06,0x07,0x08,0x09,0x0a,0x0b,0xff,0xc4,0x00,0xb5,0x10,0x00,0x02,0x01,0x03,
        0x03,0x02,0x04,0x03,0x05,0x05,0x04,0x04,0x00,0x00,0x01,0x7d,0x01,0x02,0x03,0x00,
        0x04,0x11,0x05,0x12,0x21,0x31,0x41,0x06,0x13,0x51,0x61,0x07,0x22,0x71,0x14,0x32,
        0x81,0x91,0xa1,0x08,0x23,0x42,0xb1,0xc1,0x15,0x52,0xd1,0xf0,0x24,0x33,0x62,0x72,
        0x82,0x09,0x0a,0x16,0x17,0x18,0x19,0x1a,0x25,0x26,0x27,0x28,0x29,0x2a,0x34,0x35,
        0x36,0x37,0x38,0x39,0x3a,0x43,0x44,0x45,0x46,0x47,0x48,0x49,0x4a,0x53,0x54,0x55,
        0x56,0x57,0x58,0x59,0x5a,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x73,0x74,0x75,
        0x76,0x77,0x78,0x79,0x7a,0x83,0x84,0x85,0x86,0x87,0x88,0x89,0x8a,0x93,0x94,0x95,
        0x96,0x97,0x98,0x99,0x9a,0xa2,0xa3,0xa4,0xa5,0xa6,0xa7,0xa8,0xa9,0xaa,0xb2,0xb3,
        0xb4,0xb5,0xb6,0xb7,0xb8,0xb9,0xba,0xc2,0xc3,0xc4,0xc5,0xc6,0xc7,0xc8,0xc9,0xca,
        0xd2,0xd3,0xd4,0xd5,0xd6,0xd7,0xd8,0xd9,0xda,0xe1,0xe2,0xe3,0xe4,0xe5,0xe6,0xe7,
        0xe8,0xe9,0xea,0xf1,0xf2,0xf3,0xf4,0xf5,0xf6,0xf7,0xf8,0xf9,0xfa,0xff,0xda,0x00,
        0x08,0x01,0x01,0x00,0x00,0x3f,0x00,0xfb,0xd2,0x8a,0x28,0x03,0xff,0xd9
    ])
    try:
        label, score = real_vision_check(test_image, "test")
        return {"status": "Vision API OK", "top_label": label, "score": score}
    except Exception as e:
        return {"status": "Vision API FAILED", "error": str(e)}


# ── Alarm trigger ──────────────────────────────────────────────────────────────

@app.post("/alarms/trigger/{alarm_id}", response_model=TriggerResponse)
def trigger_alarm(alarm_id: str):
    """Trigger an alarm: pick a random room object and create a session."""
    try:
        alarm = Alarm.objects.get(id=alarm_id, is_active=True)
    except Alarm.DoesNotExist:
        raise HTTPException(status_code=404, detail="Alarm not found")

    objects = list(RoomObjects.objects.filter(is_active=True))
    if not objects:
        raise HTTPException(
            status_code=400,
            detail="No room objects configured. Add some via /admin or POST /room-objects",
        )

    chosen = random.choice(objects)
    session = AlarmSession.objects.create(
        alarm=alarm,
        assigned_object=chosen,
        status="triggered",
        triggered_at=datetime.now(timezone.utc),
    )
    return TriggerResponse(
        session_id=str(session.id),
        object_name=chosen.name,
        object_emoji=chosen.emoji,
        hint=chosen.hint,
        category=chosen.category,
    )


# ── Photo verification ─────────────────────────────────────────────────────────

@app.post("/sessions/{session_id}/verify", response_model=VerifyResponse)
async def verify_photo(session_id: str, file: UploadFile = File(...)):
    """Upload a photo to verify the user photographed the correct object."""
    import traceback

    # Read the file bytes first (this is the only truly async part)
    image_bytes = await file.read()

    # All Django ORM calls must run in a thread — Django ORM is synchronous
    # and cannot be called from an async context directly
    def handle_verify():
        try:
            session = AlarmSession.objects.get(id=session_id, status="triggered")
        except AlarmSession.DoesNotExist:
            raise HTTPException(status_code=404, detail="Session not found or already resolved")

        if not session.assigned_object:
            raise HTTPException(status_code=400, detail="No object assigned to this session")

        # Save image to disk
        ext = Path(file.filename).suffix if file.filename else ".jpg"
        photo_path = MEDIA_DIR / f"{session_id}{ext}"
        photo_path.write_bytes(image_bytes)

        target = session.assigned_object
        print(f"[verify] session={session_id} target={target.name}")

        try:
            detected_label, confidence = real_vision_check(image_bytes, target.name)
            print(f"[verify] vision result: label={detected_label} confidence={confidence}")
        except Exception as e:
            traceback.print_exc()
            return VerifyResponse(
                success=False,
                message=f"Vision API error: {str(e)}",
                detected_label="error",
                confidence=0.0,
                session_id=session_id,
            )

        success = confidence >= 0.65
        session.photo_path = str(photo_path)
        session.ai_detected_label = detected_label
        session.ai_confidence = confidence
        if success:
            session.status = "solved"
            session.solved_at = datetime.now(timezone.utc)
        session.save()

        return VerifyResponse(
            success=success,
            message="Great! Alarm dismissed!" if success else f"That doesn't look like a {target.name}. Try again!",
            detected_label=detected_label,
            confidence=round(confidence, 2),
            session_id=session_id,
        )

    return await run_in_threadpool(handle_verify)


# ── Snooze ─────────────────────────────────────────────────────────────────────

@app.post("/sessions/{session_id}/snooze")
def snooze_session(session_id: str):
    """Snooze for 5 minutes — increments snooze count on alarm."""
    try:
        session = AlarmSession.objects.get(id=session_id, status="triggered")
    except AlarmSession.DoesNotExist:
        # FIX 3: was "staus_code" (typo) → "status_code"
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "snoozed"
    session.save()

    alarm = session.alarm
    alarm.snooze_count += 1
    alarm.save()

    return {"message": "Snoozed for 5 minutes 😴", "snooze_count": alarm.snooze_count}


# ── Session status ─────────────────────────────────────────────────────────────

@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    try:
        session = AlarmSession.objects.get(id=session_id)
    except AlarmSession.DoesNotExist:
        raise HTTPException(status_code=404, detail="Session not found")

    obj = session.assigned_object
    return {
        "session_id": str(session.id),
        "status": session.status,
        "object": {"name": obj.name, "emoji": obj.emoji, "hint": obj.hint} if obj else None,
        "triggered_at": session.triggered_at.isoformat() if session.triggered_at else None,
        "solved_at": session.solved_at.isoformat() if session.solved_at else None,
    }


# ── Alarm CRUD ─────────────────────────────────────────────────────────────────

@app.get("/alarms")
def list_alarms():
    alarms = Alarm.objects.filter(is_active=True).order_by("time")
    return [
        {
            "id": str(a.id),
            "label": a.label,
            "time": str(a.time)[:5],
            "days": a.days,
            "is_active": a.is_active,
            "snooze_count": a.snooze_count,
        }
        for a in alarms
    ]


@app.post("/alarms")
def create_alarm(data: AlarmCreateSchema):
    from datetime import time as dtime
    h, m = map(int, data.time.split(":"))
    alarm = Alarm.objects.create(label=data.label, time=dtime(h, m), days=data.days)
    return {"id": str(alarm.id), "label": alarm.label, "time": str(alarm.time)[:5], "days": alarm.days}


@app.patch("/alarms/{alarm_id}")
def update_alarm(alarm_id: str, data: dict):
    try:
        alarm = Alarm.objects.get(id=alarm_id)
        if "is_active" in data:
            alarm.is_active = data["is_active"]
        if "label" in data:
            alarm.label = data["label"]
        alarm.save()
        return {"id": str(alarm.id), "is_active": alarm.is_active}
    except Alarm.DoesNotExist:
        raise HTTPException(status_code=404, detail="Not found")


@app.delete("/alarms/{alarm_id}")
def delete_alarm(alarm_id: str):
    try:
        alarm = Alarm.objects.get(id=alarm_id)
        alarm.is_active = False
        alarm.save()
        return {"message": "Alarm deactivated"}
    except Alarm.DoesNotExist:
        raise HTTPException(status_code=404, detail="Not found")


# ── Room objects ───────────────────────────────────────────────────────────────

@app.get("/room-objects")
def list_room_objects():
    return [
        {"id": o.id, "name": o.name, "emoji": o.emoji, "category": o.category, "hint": o.hint}
        for o in RoomObjects.objects.filter(is_active=True)
    ]


@app.post("/room-objects")
def create_room_object(data: dict):
    obj = RoomObjects.objects.create(
        name=data["name"],
        category=data.get("category", "other"),
        # FIX 2: was data['nme'] (typo) → data['name']
        hint=data.get("hint", f"Find the {data['name']} in your room"),
        emoji=data.get("emoji", "📦"),
        description=data.get("description", ""),
    )
    return {"id": obj.id, "name": obj.name, "emoji": obj.emoji, "hint": obj.hint}


# ── Google Vision ──────────────────────────────────────────────────────────────


def real_vision_check(image_bytes: bytes, target_name: str) -> tuple[str, float]:
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"

    body = {
        "requests": [
            {
                "image": {"content": base64.b64encode(image_bytes).decode()},
                "features": [{"type": "LABEL_DETECTION", "maxResults": 20}],
            }
        ]
    }

    response = requests.post(url, json=body, timeout=10)

    if not response.ok:
        raise RuntimeError(
            f"Google Vision API error {response.status_code}: {response.text[:300]}"
        )

    result = response.json()
    labels = result.get("responses", [{}])[0].get("labelAnnotations", [])

    print(f"[vision] top labels: {[(l['description'], round(l['score'],2)) for l in labels[:5]]}")

    target = target_name.lower()

    # ✅ Synonyms mapping (VERY IMPORTANT)
    synonyms = {
        "keyboard": ["keyboard", "computer keyboard"],
        "chair": ["chair", "seat"],
        "plant": ["plant", "flowerpot", "houseplant"],
        "bottle": ["bottle", "water bottle"],
        "shoes": ["shoe", "sneaker", "footwear"],
        "pillow": ["pillow", "cushion"],
        "lamp": ["lamp", "light"],
    }

    valid_labels = synonyms.get(target, [target])

    # ✅ Strict matching
    for label in labels:
        desc = label["description"].lower()
        score = label["score"]

        if any(v in desc for v in valid_labels):
            if score >= 0.6:
                return label["description"], score

    # ❌ If no valid match → FAIL
    return "unknown", 0.0