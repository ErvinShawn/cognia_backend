from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from src.db import engine
from src.models import DeviceCreate, DeviceUpdate

router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)

# ---------------- CREATE ----------------
@router.post("/")
def create_device(device: DeviceCreate):
    with engine.connect() as conn:
        try:
            conn.execute(
                text("""
                    INSERT INTO devices (device_id, user_id) 
                    VALUES (:device_id, :user_id)
                """),
                {"device_id": device.device_id, "user_id": device.user_id}
            )
            conn.commit()
            return {"message": "Device registered successfully", "device_id": device.device_id}
        except Exception:
            raise HTTPException(status_code=400, detail="Device ID already exists or invalid user_id.")

# ---------------- READ (Single) ----------------
@router.get("/{device_id}")
def get_device(device_id: str):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM devices WHERE device_id = :device_id"),
            {"device_id": device_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Device not found")
            
        return dict(result._mapping)

# ---------------- READ (User's Devices) ----------------
@router.get("/user/{user_id}")
def get_user_devices(user_id: int):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM devices WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchall()
        
        return [dict(row._mapping) for row in result]

# ---------------- UPDATE (Heartbeat/Settings) ----------------
@router.patch("/{device_id}")
def update_device(device_id: str, updates: DeviceUpdate):
    update_data = updates.dict(exclude_unset=True) 
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")

    # Build dynamic query
    set_clauses = [f"{key} = :{key}" for key in update_data.keys()]
    set_query = ", ".join(set_clauses)

    with engine.connect() as conn:
        # Check existence
        exists = conn.execute(
            text("SELECT 1 FROM devices WHERE device_id = :device_id"),
            {"device_id": device_id}
        ).fetchone()
        
        if not exists:
            raise HTTPException(status_code=404, detail="Device not found")

        # Update and refresh 'last_seen'
        query = text(f"""
            UPDATE devices 
            SET {set_query}, last_seen = CURRENT_TIMESTAMP
            WHERE device_id = :device_id
        """)
        
        update_params = {**update_data, "device_id": device_id}
        conn.execute(query, update_params)
        conn.commit()

    return {"message": "Live status updated", "fields": list(update_data.keys())}