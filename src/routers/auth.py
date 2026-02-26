from fastapi import APIRouter
from sqlalchemy import text
from src.db import engine
from src.models import UserSignup, UserSignin

router = APIRouter(prefix="/auth", tags=["Auth"])

#signup
@router.post("/signup")
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
        "name": db_user["name"]
    }