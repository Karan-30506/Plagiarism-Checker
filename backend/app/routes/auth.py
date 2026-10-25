from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import traceback
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, Token, UserResponse
from app.supabase_client import supabase
from app.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", response_model=UserResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        # 1. Create account in Supabase Auth
        auth_res = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
        })
        
        if not auth_res or not auth_res.user:
            raise HTTPException(status_code=400, detail="User registration failed")

        user_id = auth_res.user.id

        # 2. Synchronize user profile into PostgreSQL public.users table
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            db_user = User(
                id=user_id,
                email=user_data.email,
                full_name=user_data.full_name
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)

        return db_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("\n--- SIGNUP ERROR TRACEBACK ---")
        traceback.print_exc()
        print("-----------------------------\n")
        
        # Extract clean error message from Supabase AuthApiError
        error_msg = getattr(e, "message", str(e))
        raise HTTPException(status_code=400, detail=error_msg)

@router.post("/login", response_model=Token)
def login(user_data: UserLogin):
    try:
        auth_res = supabase.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password,
        })
        
        if not auth_res or not auth_res.session:
            raise HTTPException(status_code=401, detail="Invalid credentials or unconfirmed email")

        return Token(
            access_token=auth_res.session.access_token,
            user_id=auth_res.user.id
        )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = getattr(e, "message", "Invalid email or password")
        raise HTTPException(status_code=401, detail=error_msg)

@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == current_user["id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User profile not found")
    return db_user