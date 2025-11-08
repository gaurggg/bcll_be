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
    capacity: int = 70  # Updated: Average bus capacity in India
    status: Literal["active", "inactive"] = "active"

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class PathStop(BaseModel):
    stop_id: str
    sequence: int
    distance_km: float


class IntermediateStop(BaseModel):
    """Stop along a route with location and timing information"""
    name: str
    lat: float
    lng: float
    sequence: int  # Order in the route
    distance_from_start_km: float
    estimated_time_from_start_min: int  # ETA from route start


class Route(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    route_id: str
    name: str
    source_stop_id: str
    dest_stop_id: str
    path: List[PathStop]
    intermediate_stops: Optional[List[IntermediateStop]] = []  # NEW: Stops with timing
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


class BusInstance(BaseModel):
    """Individual bus running on a route"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    bus_instance_id: str  # e.g., "R1-B1", "R1-B2"
    route_id: str
    bus_number: str
    bus_id: str
    deployment_sequence: int  # 1st, 2nd, 3rd bus on this route
    schedule_offset_min: int  # Time offset from first bus
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class StopTiming(BaseModel):
    """Timing at a specific stop"""
    stop_name: str
    stop_lat: float
    stop_lng: float
    arrival_time: str  # HH:MM format
    departure_time: str  # HH:MM format


class Schedule(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    route_id: str
    bus_id: str
    bus_instance_id: Optional[str] = None  # NEW: Links to specific bus instance
    peak_hour: Literal["morning", "evening", "off-peak"]
    start_time: str
    end_time: Optional[str] = None
    frequency_min: int
    suggested_buses_count: int
    departure_times: Optional[List[str]] = []  # All departure times
    stop_timings: Optional[List[StopTiming]] = []  # NEW: Time at each stop
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


class TripLeg(BaseModel):
    """Single leg of a multi-leg journey"""
    route_id: str
    route_name: str
    bus_number: str
    source_name: str
    source_lat: float
    source_lng: float
    dest_name: str
    dest_lat: float
    dest_lng: float
    distance_km: float
    fare: float
    boarding_time: Optional[str] = None


class TravelHistory(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    passenger_id: str
    route_id: str
    source_stop_id: str
    dest_stop_id: str
    source_name: Optional[str] = None  # NEW: Location names
    dest_name: Optional[str] = None
    source_lat: Optional[float] = None  # NEW: Coordinates
    source_lng: Optional[float] = None
    dest_lat: Optional[float] = None
    dest_lng: Optional[float] = None
    travel_time: str
    day_of_week: str
    trip_legs: Optional[List[TripLeg]] = []  # NEW: Multi-leg journey support
    total_fare: Optional[float] = None
    is_multi_leg: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class CurrentTrip(BaseModel):
    """Track passenger's current/active trip"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    passenger_id: str
    current_route_id: str
    current_bus_number: str
    source_name: str
    source_lat: float
    source_lng: float
    final_destination_name: str
    final_dest_lat: float
    final_dest_lng: float
    current_location_name: Optional[str] = None  # Where passenger is now
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    completed_legs: List[TripLeg] = []
    total_fare_so_far: float = 0.0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

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


class MultiBusDeploymentRequest(BaseModel):
    """Request to deploy multiple buses on a route"""
    route_id: str
    num_buses: int  # How many buses to deploy
    frequency_min: int  # Frequency between buses
    peak_hour: Literal["morning", "evening", "off-peak"]


class InterconnectedRouteRequest(BaseModel):
    """Request to find connecting routes from current location"""
    current_lat: float
    current_lng: float
    final_dest_lat: float
    final_dest_lng: float
    current_trip_id: Optional[str] = None  # If continuing a trip

