from fastapi import FastAPI, UploadFile, File, Form
from sqlalchemy import create_engine, text
import requests
from pydantic import BaseModel


class RoutineCreate(BaseModel):
    device_id: str
    patient_id: str
    step : str


class RoutineStepCreate(BaseModel):
    routine_id: int
    routine_step: str


class RoutineStepUpdate(BaseModel):
    step_id: int
    routine_step: str


app = FastAPI()


DATABASE_URL = "postgresql://postgres:abc123@localhost/cognia_test"
engine = create_engine(DATABASE_URL)


CLOUD_NAME = "diq0bcrjl"
UPLOAD_PRESET = "Test_Preset"


@app.post("/routines/create")
def create_routine(data: RoutineCreate):

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                INSERT INTO routines (device_id, patient_id)
                VALUES (:device, :patient)
                RETURNING routine_id
            """),
            {
                "device": data.device_id,
                "patient": data.patient_id
            }
        )

        routine_id = result.scalar()
        conn.commit()

        conn.execute(
            text("""
                INSERT INTO routine_steps (routine_id, routine_step)
                VALUES (:rid, :step)
            """),
            {
                "rid": routine_id,
                "step": data.step
            }
        )
        conn.commit()

    return {
        "message": "routine created",
        "routine_id": routine_id
    }


@app.post("/routines/add-step")
def add_routine_step(data: RoutineStepCreate):

    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO routine_steps (routine_id, routine_step)
                VALUES (:rid, :step)
            """),
            {
                "rid": data.routine_id,
                "step": data.routine_step
            }
        )
        conn.commit()

    return {"message": "step added"}


@app.put("/routines/update-step")
def update_routine_step(data: RoutineStepUpdate):

    with engine.connect() as conn:
        conn.execute(
            text("""
                UPDATE routine_steps
                SET routine_step = :step
                WHERE step_id = :id
            """),
            {
                "step": data.routine_step,
                "id": data.step_id
            }
        )
        conn.commit()

    return {"message": "step updated"}


@app.delete("/routines/delete-step")
def delete_routine_step(step_id: int):

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                DELETE FROM routine_steps
                WHERE step_id = :id
                RETURNING step_id
            """),
            {"id": step_id}
        )

        deleted = result.fetchone()
        conn.commit()

    if not deleted:
        return {"message": "step not found"}

    return {"message": "step deleted", "step_id": step_id}


@app.delete("/routines/delete")
def delete_routine(routine_id: int):

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                DELETE FROM routines
                WHERE routine_id = :id
                RETURNING routine_id
            """),
            {"id": routine_id}
        )

        deleted = result.fetchone()
        conn.commit()

    if not deleted:
        return {"message": "routine not found"}

    return {
        "message": "routine deleted",
        "routine_id": routine_id,
        "note": "all steps removed automatically"
    }