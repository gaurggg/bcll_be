from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class Location(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]


class Stop(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    location: Location
    type: Literal["major", "regular"] = "regular"
    avg_dwell_time_s: int = 45

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Bus(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    bus_number: str
    capacity: int = 50
    status: Literal["active", "inactive"] = "active"

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class PathStop(BaseModel):
    stop_id: str
    sequence: int
    distance_km: float


class Route(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    route_id: str
    name: str
    source_stop_id: str
    dest_stop_id: str
    path: List[PathStop]
    total_distance_km: float
    estimated_duration_min: int
    gemini_score: Optional[float] = None
    traffic_score: Optional[float] = None
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Schedule(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    route_id: str
    bus_id: str
    peak_hour: Literal["morning", "evening", "off-peak"]
    start_time: str
    frequency_min: int
    suggested_buses_count: int
    active: bool = True

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Passenger(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    email: EmailStr
    phone: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class TravelHistory(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    passenger_id: str
    route_id: str
    source_stop_id: str
    dest_stop_id: str
    travel_time: str
    day_of_week: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class FareConfig(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    distance_slab_km: List[float] = [0, 5, 10, 20, 50]
    base_fare_inr: List[float] = [10, 15, 25, 40]
    peak_multiplier: float = 1.2

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# Request/Response Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoutePlanRequest(BaseModel):
    source_lat: float
    source_lng: float
    dest_lat: float
    dest_lng: float
    peak_hour: Optional[Literal["morning", "evening", "off-peak"]] = None


class ScheduleCreateRequest(BaseModel):
    route_id: str
    peak_hour: Literal["morning", "evening", "off-peak"]


class BusSearchRequest(BaseModel):
    source_lat: float
    source_lng: float
    dest_lat: float
    dest_lng: float


class FareRequest(BaseModel):
    distance_km: float
    is_peak_hour: bool = False

