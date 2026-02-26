from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from src.db import engine
from pydantic import BaseModel

router = APIRouter(prefix="/faces", tags=["Faces"])


# ---------- MODEL ----------
class FaceCreate(BaseModel):
    person_name: str
    relationship: str
    image_url: str


# ---------- CREATE FACE ----------
@router.post("")
def create_face(data: FaceCreate):
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO faces (person_name, relationship, image_url)
                    VALUES (:person_name, :relationship, :image_url)
                    RETURNING id
                """),
                data.model_dump()
            )

            face_id = result.scalar()
            conn.commit()

        return {
            "message": "face saved",
            "id": face_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- GET ALL ----------
@router.get("")
def get_faces():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM faces ORDER BY id DESC"))
        return [dict(row._mapping) for row in result]


# ---------- DELETE FACE ----------
@router.delete("/{face_id}")
def delete_face(face_id: int):
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM faces WHERE id = :id RETURNING id"),
            {"id": face_id}
        )
        deleted = result.fetchone()
        conn.commit()

    if not deleted:
        raise HTTPException(status_code=404, detail="Face not found")

    return {"message": "face deleted"}