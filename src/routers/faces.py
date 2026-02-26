from fastapi import APIRouter, UploadFile, File, Form
from sqlalchemy import text
from src.db import engine
import requests
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/faces", tags=["Faces"])

CLOUD_NAME = os.getenv("CLOUD_NAME")
UPLOAD_PRESET = os.getenv("UPLOAD_PRESET")

@router.post("/upload")
async def upload_face(
    person_name: str = Form(...),
    image: UploadFile = File(...)
):
    files = {"file": image.file}
    data = {"upload_preset": UPLOAD_PRESET}

    res = requests.post(
        f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/image/upload",
        files=files,
        data=data
    )

    image_url = res.json()["secure_url"]

    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO faces (person_name, image_url) VALUES (:name, :url)"),
            {"name": person_name, "url": image_url}
        )
        conn.commit()

    return {"image_url": image_url}

@router.get("")
def get_faces():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM faces"))
        return [dict(row._mapping) for row in result]