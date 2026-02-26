from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from src.db import engine
from pydantic import BaseModel
from typing import List, Optional


class ReminderSchema(BaseModel):
    title: str
    description: Optional[str] = None
    time: str

class RoutineUpdate(BaseModel):
    device_id: str
    user_id: int
    reminder: ReminderSchema
router = APIRouter(prefix="/routines", tags=["Routines"])

@router.post("/save")
def save_reminder(data: RoutineUpdate):
    with engine.connect() as conn:
        try:
            query = text("""
                INSERT INTO routines (device_id, user_id, reminders)
                VALUES (:d, :u, jsonb_build_array(jsonb_build_object(
                    'title', :title, 'description', :desc, 'time', :time
                )))
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    reminders = routines.reminders || jsonb_build_object(
                        'title', :title, 'description', :desc, 'time', :time
                    ),
                    updated_at = CURRENT_TIMESTAMP
            """)
            
            conn.execute(query, {
                "d": data.device_id,
                "u": data.user_id,
                "title": data.reminder.title,
                "desc": data.reminder.description,
                "time": data.reminder.time
            })
            conn.commit()
            return {"status": "success"}
        except Exception as e:
            print(f"Error saving routine: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}")
def get_reminders(user_id: int):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT reminders FROM routines WHERE user_id = :u"),
            {"u": user_id}
        ).fetchone()
        
        return result[0] if result else []