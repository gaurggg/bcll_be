from fastapi import APIRouter, HTTPException, status
from app.db.models import LoginRequest, RegisterRequest, TokenResponse
from app.db.mongodb import mongodb
from app.utils.auth_utils import hash_password, verify_password, create_access_token
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/admin/login", response_model=TokenResponse)
async def admin_login(request: LoginRequest):
    """Admin login"""
    # For POC, hardcode admin credentials
    # In production, store in database with proper security
    ADMIN_EMAIL = "atinitytech.business@gmail.com"
    ADMIN_PASSWORD = "atinity@123"  # This should be hashed in production
    
    if request.email != ADMIN_EMAIL or request.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token = create_access_token(
        data={"sub": request.email, "email": request.email},
        role="admin"
    )
    
    return TokenResponse(access_token=token)


@router.post("/passenger/register", response_model=TokenResponse)
async def passenger_register(request: RegisterRequest):
    """Register a new passenger"""
    passengers_collection = mongodb.get_collection("passengers")
    
    # Check if email already exists
    existing = passengers_collection.find_one({"email": request.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create passenger
    passenger = {
        "name": request.name,
        "email": request.email,
        "phone": request.phone,
        "password_hash": hash_password(request.password),
        "created_at": datetime.utcnow()
    }
    
    result = passengers_collection.insert_one(passenger)
    passenger_id = str(result.inserted_id)
    
    # Create token
    token = create_access_token(
        data={"sub": passenger_id, "email": request.email},
        role="passenger"
    )
    
    return TokenResponse(access_token=token)


@router.post("/passenger/login", response_model=TokenResponse)
async def passenger_login(request: LoginRequest):
    """Passenger login"""
    passengers_collection = mongodb.get_collection("passengers")
    
    passenger = passengers_collection.find_one({"email": request.email})
    if not passenger:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not verify_password(request.password, passenger["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token = create_access_token(
        data={"sub": str(passenger["_id"]), "email": passenger["email"]},
        role="passenger"
    )
    
    return TokenResponse(access_token=token)

