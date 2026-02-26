from fastapi import FastAPI
from src.routers import faces, routines, geofence, auth
from src.db import engine
from sqlalchemy import text

app = FastAPI()

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