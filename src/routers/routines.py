from fastapi import APIRouter
from sqlalchemy import text
from src.db import engine
from src.models import RoutineCreate, RoutineStepCreate

router = APIRouter(prefix="/routines", tags=["Routines"])

@router.post("/create")
def create_routine(data: RoutineCreate):
    with engine.connect() as conn:
        # 1. Create the Master Routine entry
        result = conn.execute(
            text("INSERT INTO routines (device_id, patient_id) VALUES (:d, :p) RETURNING routine_id"),
            {"d": data.device_id, "p": data.patient_id}
        )
        routine_id = result.scalar()

        # 2. Add the first reminder to routine_steps
        conn.execute(
            text("""
                INSERT INTO routine_steps (routine_id, title, description, scheduled_time)
                VALUES (:rid, :title, :desc, :time)
            """),
            {
                "rid": routine_id,
                "title": data.step.title,
                "desc": data.step.description,
                "time": data.step.time
            }
        )
        conn.commit()
    return {"message": "Master routine created", "routine_id": routine_id}

@router.post("/add-step")
def add_routine_step(data: RoutineStepCreate):
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO routine_steps (routine_id, title, description, scheduled_time)
                VALUES (:rid, :title, :desc, :time)
            """),
            {
                "rid": data.routine_id,
                "title": data.title,
                "desc": data.description,
                "time": data.time
            }
        )
        conn.commit()
    return {"message": "Reminder added to routine"}