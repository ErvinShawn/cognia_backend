from argon2 import hash_password
from fastapi import FastAPI, UploadFile, File, Form
from sqlalchemy import create_engine, text
import requests
from pydantic import BaseModel

class UserSignup(BaseModel):
    name: str
    email: str
    password: str

class UserSignin(BaseModel):
    email: str
    password: str

class Geofence(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    radius_meters: float


app = FastAPI()


DATABASE_URL = "postgresql://postgres:abc123@localhost/cognia_test"
engine = create_engine(DATABASE_URL)


CLOUD_NAME = "diq0bcrjl"
UPLOAD_PRESET = "Test_Preset"



@app.post("/faces/upload")
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

    cloudinary_response = res.json()
    image_url = cloudinary_response["secure_url"]

    # store url in postgres
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO faces (person_name, image_url) VALUES (:name, :url)"),
            {"name": person_name, "url": image_url}
        )
        conn.commit()

    return {
        "message": "face uploaded",
        "image_url": image_url
    }



@app.get("/faces")
def get_faces():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM faces"))
        return [dict(row._mapping) for row in result]
    
    



@app.post("/geofence/set")
def set_geofence(data: Geofence):

    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO geofences (device_id, latitude, longitude, radius_meters) VALUES (:device_id, :lat, :lon, :radius)"),
            {
                "device_id": data.device_id,
                "lat": data.latitude,
                "lon": data.longitude,
                "radius": data.radius_meters
            }
        )
        conn.commit()

    return {
        "message": "geofence saved",
        "device_id": data.device_id,
        "center": [data.latitude, data.longitude],
        "radius_meters": data.radius_meters
    }



@app.post("/auth/signup")
def signup(user: UserSignup):


    try:
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO users (name, email, password)
                    VALUES (:name, :email, :password)
                """),
                {
                    "name": user.name,
                    "email": user.email,
                    "password": user.password
                }
            )
            conn.commit()

        return {"message": "user created"}

    except Exception as e:
        print("ERROR:", e)
        return {"error": str(e)}
    

@app.post("/auth/signin")
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
        "name": db_user["name"]
    }