from pydantic import BaseModel

# ---------- AUTH ----------

class UserSignup(BaseModel):
    name: str
    email: str
    password: str

class UserSignin(BaseModel):
    email: str
    password: str

# ---------- GEOFENCE ----------

class Geofence(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    radius_meters: float

# ---------- ROUTINES ----------

class RoutineCreate(BaseModel):
    device_id: str
    patient_id: str
    step: str

class RoutineStepCreate(BaseModel):
    routine_id: int
    routine_step: str

class RoutineStepUpdate(BaseModel):
    step_id: int
    routine_step: str