from fastapi import APIRouter
from sqlalchemy import text
from src.db import engine
from src.models import Geofence

router = APIRouter(prefix="/geofence", tags=["Geofence"])

@router.post("/set")
def set_geofence(data: Geofence):

    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO geofences (device_id, latitude, longitude, radius_meters)
                VALUES (:device_id, :lat, :lon, :radius)
            """),
            {
                "device_id": data.device_id,
                "lat": data.latitude,
                "lon": data.longitude,
                "radius": data.radius_meters
            }
        )
        conn.commit()

    return {"message": "geofence saved"}