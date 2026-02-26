from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from src.db import engine
from pydantic import BaseModel

router = APIRouter(prefix="/geofence", tags=["Geofence"])

class GeofenceSchema(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    radius_meters: float
@router.post("/set")
def set_geofence(data: GeofenceSchema):
    with engine.connect() as conn:
        try:
            # ✅ Removed updated_at so it doesn't crash your DB
            query = text("""
                INSERT INTO geofences (device_id, latitude, longitude, radius_meters)
                VALUES (:device_id, :lat, :lon, :radius)
                ON CONFLICT (device_id) 
                DO UPDATE SET 
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    radius_meters = EXCLUDED.radius_meters
            """)
            
            conn.execute(
                query,
                {
                    "device_id": data.device_id,
                    "lat": data.latitude,
                    "lon": data.longitude,
                    "radius": data.radius_meters
                }
            )
            conn.commit()
            return {"status": "success", "message": "Geofence synchronized"}
        except Exception as e:
            print(f"Database Error: {e}")
            raise HTTPException(status_code=500, detail="Failed to save geofence")