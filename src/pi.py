from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from src.db import engine
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import httpx
import json
import math

router = APIRouter(prefix="/events", tags=["Events"])

class FaceRecognitionEvent(BaseModel):
    device_id: str
    user_id: int
    patient_id: int
    person_name: Optional[str] = None
    confidence: float
    is_known: bool
    image_url: Optional[str] = None


class DetectedObject(BaseModel):
    label: str
    confidence: float
    bbox: Optional[List[float]] = None


class ObjectDetectionEvent(BaseModel):
    device_id: str
    user_id: int
    patient_id: int
    objects: List[DetectedObject]


class FallDetectedEvent(BaseModel):
    device_id: str
    user_id: int
    patient_id: int
    impact_force: float
    orientation_change: float
    confidence: float
    ax: Optional[float] = None
    ay: Optional[float] = None
    az: Optional[float] = None


class DeviceLocation(BaseModel):
    device_id: str
    user_id: int
    patient_id: int
    latitude: float
    longitude: float




def _now():
    return datetime.now(timezone.utc)


def _validate_device(device_id: str):
    """Ensure device exists"""
    with engine.connect() as conn:
        device = conn.execute(
            text("SELECT device_id FROM devices WHERE device_id = :did"),
            {"did": device_id}
        ).fetchone()

    if not device:
        raise HTTPException(status_code=401, detail="Unknown device")


def _store_event(event_type: str, user_id: int, device_id: str, data: dict) -> int:
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO events (event_type, user_id, device_id, data_json, timestamp)
                VALUES (:event_type, :user_id, :device_id, :data::jsonb, :timestamp)
                RETURNING id
            """),
            {
                "event_type": event_type,
                "user_id": user_id,
                "device_id": device_id,
                "data": json.dumps(data),
                "timestamp": _now(),
            }
        )
        event_id = result.scalar()

    return event_id


async def _push(user_id: int, title: str, body: str, data: dict):
    """Send Expo push notifications"""

    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT token FROM push_tokens WHERE user_id = :uid"),
            {"uid": user_id}
        ).fetchall()

    tokens = [r[0] for r in rows]

    if not tokens:
        return

    messages = [
        {
            "to": token,
            "title": title,
            "body": body,
            "data": data,
            "sound": "default"
        }
        for token in tokens
    ]

    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                "https://exp.host/--/api/v2/push/send",
                json=messages,
                headers={"Content-Type": "application/json"},
                timeout=8,
            )
        except Exception as e:
            print(f"[Push Error] {e}")


def calculate_distance(lat1, lon1, lat2, lon2):
    """Haversine formula"""
    R = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))





@router.post("/face-recognition")
async def face_recognition_event(payload: FaceRecognitionEvent):

    _validate_device(payload.device_id)

    data = payload.model_dump()

    event_id = _store_event(
        "face_recognition",
        payload.user_id,
        payload.device_id,
        data
    )

    if not payload.is_known:

        await _push(
            user_id=payload.user_id,
            title="Unknown Person Detected",
            body="An unrecognised person was detected near the patient.",
            data={
                "event_id": event_id,
                "type": "face_recognition"
            }
        )

    return {"event_id": event_id, "received": True}


@router.post("/object-detection")
async def object_detection_event(payload: ObjectDetectionEvent):

    _validate_device(payload.device_id)

    data = payload.model_dump()

    event_id = _store_event(
        "object_detection",
        payload.user_id,
        payload.device_id,
        data
    )

    alert_labels = {"pill bottle", "medication", "pills"}

    detected = {obj.label.lower() for obj in payload.objects}

    if alert_labels & detected:

        await _push(
            user_id=payload.user_id,
            title="Medication Detected",
            body="Medication was spotted near the patient.",
            data={
                "event_id": event_id,
                "type": "object_detection"
            }
        )

    return {"event_id": event_id, "received": True}


@router.post("/fall-detected")
async def fall_detected_event(payload: FallDetectedEvent):

    _validate_device(payload.device_id)

    data = payload.model_dump()

    event_id = _store_event(
        "fall_detected",
        payload.user_id,
        payload.device_id,
        data
    )

    await _push(
        user_id=payload.user_id,
        title="Fall Detected!",
        body="A fall has been detected. Please check on the patient immediately.",
        data={
            "event_id": event_id,
            "type": "fall_detected"
        }
    )

    return {"event_id": event_id, "received": True}


@router.post("/geofence-check")
async def geofence_check(location: DeviceLocation):

    _validate_device(location.device_id)

    # Home location (replace with DB later)
    home_lat = 15.2993
    home_lng = 74.2201

    safe_radius = 100  # meters

    distance = calculate_distance(
        location.latitude,
        location.longitude,
        home_lat,
        home_lng
    )

    if distance > safe_radius:

        data = {
            "device_id": location.device_id,
            "patient_id": location.patient_id,
            "current_lat": location.latitude,
            "current_lng": location.longitude,
            "home_lat": home_lat,
            "home_lng": home_lng,
            "distance_meters": distance,
            "safe_radius": safe_radius
        }

        event_id = _store_event(
            "geofence_alert",
            location.user_id,
            location.device_id,
            data
        )

        await _push(
            user_id=location.user_id,
            title="Geofence Alert",
            body=f"Patient is {distance:.0f}m outside safe zone.",
            data={
                "event_id": event_id,
                "type": "geofence_alert",
                "lat": location.latitude,
                "lng": location.longitude
            }
        )

        return {
            "status": "breach",
            "distance": distance
        }

    return {
        "status": "inside",
        "distance": distance
    }




@router.get("/user/{user_id}")
def get_events(user_id: int, event_type: Optional[str] = None, limit: int = 50):

    query = "SELECT * FROM events WHERE user_id = :uid"
    params = {"uid": user_id}

    if event_type:
        query += " AND event_type = :etype"
        params["etype"] = event_type

    query += " ORDER BY timestamp DESC LIMIT :limit"
    params["limit"] = limit

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).fetchall()

    return [dict(r._mapping) for r in rows]