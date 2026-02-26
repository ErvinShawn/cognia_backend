from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import faces, routines, geofence, auth, devices
from src.db import engine
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (perfect for local development)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PATCH, etc.)
    allow_headers=["*"],  # Allows all headers
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def test_db_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ DATABASE CONNECTED SUCCESSFULLY")

    except Exception as e:
        print("❌ DATABASE CONNECTION FAILED")
        print(e)

app.include_router(faces.router)
app.include_router(routines.router)
app.include_router(geofence.router)
app.include_router(auth.router)
app.include_router(devices.router)