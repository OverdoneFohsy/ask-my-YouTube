from fastapi import APIRouter, HTTPException
from app.core.supabase_client import get_supabase
from app.schemas.auth import AuthSchema

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup")
async def signup(data: AuthSchema):
    supabase = get_supabase()

    response = supabase.auth.sign_up({"email": data.email, "password": data.password})
    if not response.user:
        raise HTTPException(status_code=400, detail="Signup failed")
    return {"message": "Verification email sent! Please check your inbox."}

@router.post("/login")
async def login(data: AuthSchema):
    supabase = get_supabase()

    response = supabase.auth.sign_in_with_password({"email": data.email, "password": data.password})
    if not response.session:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "access_token": response.session.access_token,
        "token_type": "bearer"
    }