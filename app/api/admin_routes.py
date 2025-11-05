from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from datetime import datetime
from app.db.models import RoutePlanRequest, ScheduleCreateRequest
from app.db.mongodb import mongodb
from app.utils.auth_utils import require_admin
from app.routing.graph_builder import graph_builder
from app.ai.gemini_route_optimizer import gemini_route_optimizer
from app.ai.gemini_scheduler import gemini_scheduler

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


@router.post("/route/plan")
async def plan_route(request: RoutePlanRequest):
    """
    AI-assisted route planning
    Returns top 5 optimized routes using Dijkstra + Gemini AI
    """
    try:
        origin = (request.source_lat, request.source_lng)
        destination = (request.dest_lat, request.dest_lng)
        
        # Get alternative routes from Google Maps
        routes = graph_builder.get_alternative_routes(origin, destination, k=5)
        
        if not routes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No routes found between these locations"
            )
        
        # Use Gemini AI to analyze and rank routes
        ranked_routes = gemini_route_optimizer.optimize_and_rank_routes(
            routes, origin, destination
        )
        
        return {
            "source": {"lat": request.source_lat, "lng": request.source_lng},
            "destination": {"lat": request.dest_lat, "lng": request.dest_lng},
            "total_routes": len(ranked_routes),
            "routes": ranked_routes
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error planning route: {str(e)}"
        )


@router.post("/route/create")
async def create_route(route_data: Dict[Any, Any], current_user: Dict = Depends(require_admin)):
    """
    Create a new bus route from planned route
    """
    routes_collection = mongodb.get_collection("routes")
    
    # Generate route ID
    count = routes_collection.count_documents({})
    route_id = f"R{count + 1}"
    
    # Create route document
    route = {
        "route_id": route_id,
        "name": route_data.get("name", f"Route {route_id}"),
        "source_stop_id": route_data.get("source_stop_id", ""),
        "dest_stop_id": route_data.get("dest_stop_id", ""),
        "path": route_data.get("path", []),
        "total_distance_km": route_data.get("distance_km", 0),
        "estimated_duration_min": route_data.get("duration_min", 0),
        "gemini_score": route_data.get("gemini_score", 0),
        "traffic_score": route_data.get("traffic_score", 0),
        "created_by": current_user.get("email", "admin"),
        "created_at": datetime.utcnow()
    }
    
    result = routes_collection.insert_one(route)
    route["_id"] = str(result.inserted_id)
    
    return {
        "message": "Route created successfully",
        "route_id": route_id,
        "route": route
    }


@router.post("/schedule/create")
async def create_schedule(request: ScheduleCreateRequest):
    """
    Create schedule with AI predictions for bus count and frequency
    """
    try:
        # Get route details
        routes_collection = mongodb.get_collection("routes")
        route = routes_collection.find_one({"route_id": request.route_id})
        
        if not route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )
        
        # Use Gemini AI to predict optimal scheduling
        route_data = {
            "name": route.get("name"),
            "total_distance_km": route.get("total_distance_km"),
            "estimated_duration_min": route.get("estimated_duration_min"),
            "traffic_score": route.get("traffic_score", 7.0)
        }
        
        prediction = gemini_scheduler.predict_schedule(route_data, request.peak_hour)
        
        # Create schedule document
        schedules_collection = mongodb.get_collection("schedules")
        
        # For POC, create a simple schedule
        schedule = {
            "route_id": request.route_id,
            "bus_id": "TBD",  # To be assigned
            "peak_hour": request.peak_hour,
            "start_time": "06:00",
            "frequency_min": prediction.get("frequency_min"),
            "suggested_buses_count": prediction.get("buses_needed"),
            "active": True,
            "created_at": datetime.utcnow()
        }
        
        result = schedules_collection.insert_one(schedule)
        schedule["_id"] = str(result.inserted_id)
        
        return {
            "message": "Schedule created successfully",
            "schedule": schedule,
            "ai_prediction": prediction
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating schedule: {str(e)}"
        )


@router.get("/routes")
async def get_all_routes():
    """Get all routes"""
    routes_collection = mongodb.get_collection("routes")
    routes = list(routes_collection.find())
    
    # Convert ObjectId to string
    for route in routes:
        route["_id"] = str(route["_id"])
    
    return {
        "total": len(routes),
        "routes": routes
    }


@router.get("/routes/{route_id}")
async def get_route(route_id: str):
    """Get specific route details"""
    routes_collection = mongodb.get_collection("routes")
    route = routes_collection.find_one({"route_id": route_id})
    
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    
    route["_id"] = str(route["_id"])
    return route


@router.get("/schedules")
async def get_all_schedules():
    """Get all schedules"""
    schedules_collection = mongodb.get_collection("schedules")
    schedules = list(schedules_collection.find())
    
    # Convert ObjectId to string
    for schedule in schedules:
        schedule["_id"] = str(schedule["_id"])
    
    return {
        "total": len(schedules),
        "schedules": schedules
    }


@router.put("/route/{route_id}")
async def update_route(route_id: str, route_data: Dict[Any, Any]):
    """Update a route"""
    routes_collection = mongodb.get_collection("routes")
    
    result = routes_collection.update_one(
        {"route_id": route_id},
        {"$set": route_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    
    return {
        "message": "Route updated successfully",
        "route_id": route_id
    }


@router.delete("/route/{route_id}")
async def delete_route(route_id: str):
    """Delete a route"""
    routes_collection = mongodb.get_collection("routes")
    
    result = routes_collection.delete_one({"route_id": route_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    
    return {
        "message": "Route deleted successfully",
        "route_id": route_id
    }

