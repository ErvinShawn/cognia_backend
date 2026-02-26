from fastapi import APIRouter, Form, File, UploadFile
from sqlalchemy import text
from src.db import engine
from src.models import UserSignup, UserSignin
import requests

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup")
def signup(user: UserSignup):
    try:
        with engine.connect() as conn:
            result=conn.execute(
                text("""
                    INSERT INTO users (
                        patient_name,
                        email,
                        password,
                        medical_condition,
                        emergency_contact,
                        profile_photo_url
                    )
                    VALUES (
                        :patient_name,
                        :email,
                        :password,
                        :medical_condition,
                        :emergency_contact,
                        :profile_photo_url
                    )
                     RETURNING id, patient_name, medical_condition, profile_photo_url
                """),
                user.model_dump()
            )
            new_user = result.fetchone()
            conn.commit()
            

        return {
            "message": "user created",
            "user_id": new_user.id,
            "patient_name": new_user.patient_name,
            "medical_condition": new_user.medical_condition,
            "profile_photo_url": new_user.profile_photo_url
        }

    except Exception as e:
        return {"error": str(e)}
    
#signin
@router.post("/signin")
def signin(user: UserSignin):

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": user.email}
        ).fetchone()

    if not result:
        return {"error": "invalid credentials"}

    db_user = dict(result._mapping)
    if user.password != db_user["password"]:
        return {"error": "invalid credentials"}

    return {
        "message": "login successful",
        "user_id": db_user["id"],
        "patient_name": db_user["patient_name"],
        "medical_condition": db_user["medical_condition"],
        "profile_photo_url": db_user["profile_photo_url"]
    }