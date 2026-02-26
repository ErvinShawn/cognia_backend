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
    """Register a new Raspberry Pi to a Caregiver"""
    with engine.connect() as conn:
        try:
            conn.execute(
                text("""
                    INSERT INTO devices (device_id, user_id) 
                    VALUES (:device_id, :user_id)
                """),
                {
                    "device_id": device.device_id,
                    "user_id": device.user_id
                }
            )
            conn.commit()
            return {"message": "Device registered successfully", "device_id": device.device_id}
        except Exception as e:
            raise HTTPException(status_code=400, detail="Device might already exist or user_id is invalid.")

# ---------------- READ (Single) ----------------
@router.get("/{device_id}")
def get_device(device_id: str):
    """Fetch the live status, location, and settings of a specific Pi"""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM devices WHERE device_id = :device_id"),
            {"device_id": device_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Device not found")
            
        return dict(result._mapping)

# ---------------- READ (All for a User) ----------------
@router.get("/user/{user_id}")
def get_user_devices(user_id: int):
    """Fetch all devices owned by a specific caregiver"""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM devices WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchall()
        
        return [dict(row._mapping) for row in result]

# ---------------- UPDATE (PATCH) ----------------
@router.patch("/{device_id}")
def update_device(device_id: str, updates: DeviceUpdate):
    """
    Dynamically update device location, status, or camera settings.
    Only updates the fields you actually send in the JSON!
    """
    # exclude_unset=True ignores fields you didn't include in the request
    update_data = updates.dict(exclude_unset=True) 
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided to update")

    # Dynamically build the SQL SET clause (e.g., "latitude = :latitude, status = :status")
    set_clauses = [f"{key} = :{key}" for key in update_data.keys()]
    set_query = ", ".join(set_clauses)

    with engine.connect() as conn:
        # Check if device exists first
        exists = conn.execute(
            text("SELECT 1 FROM devices WHERE device_id = :device_id"),
            {"device_id": device_id}
        ).fetchone()
        
        if not exists:
            raise HTTPException(status_code=404, detail="Device not found")

        # Execute the dynamic update and refresh the 'last_seen' timestamp automatically
        query = f"""
            UPDATE devices 
            SET {set_query}, last_seen = CURRENT_TIMESTAMP
            WHERE device_id = :device_id
        """
        
        update_data["device_id"] = device_id # Add the ID to the dictionary for the SQL query
        
        conn.execute(text(query), update_data)
        conn.commit()

    return {"message": "Device updated successfully", "updated_fields": list(update_data.keys())}