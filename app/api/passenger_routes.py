from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict
from datetime import datetime
from app.db.models import BusSearchRequest, FareRequest, TravelHistory, InterconnectedRouteRequest
from app.db.mongodb import mongodb
from app.utils.auth_utils import require_passenger, get_current_user
from app.external.google_maps_client import google_maps_client
from app.fares.fare_calculator import fare_calculator
from app.ai.gemini_recommender import gemini_recommender
from app.utils.route_connector import route_connector

router = APIRouter(prefix="/passenger", tags=["Passenger"])


@router.post("/search")
async def search_buses(request: BusSearchRequest, current_user: Dict = Depends(get_current_user)):
    """
    Search for buses between source and destination
    Returns available routes with ETA, fare, bus numbers, and route details
    """
    try:
        origin = (request.source_lat, request.source_lng)
        destination = (request.dest_lat, request.dest_lng)

        # Get distance and duration from Google Maps
        distance_data = google_maps_client.get_distance_matrix([origin], [destination])

        if not distance_data or "rows" not in distance_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not calculate distance"
            )

        element = distance_data["rows"][0]["elements"][0]
        if element["status"] != "OK":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No route found"
            )

        distance_km = element["distance"]["value"] / 1000
        duration_min = element["duration"]["value"] / 60

        # Get all active routes from database
        routes_collection = mongodb.get_collection("routes")
        buses_collection = mongodb.get_collection("buses")
        schedules_collection = mongodb.get_collection("schedules")

        all_routes = list(routes_collection.find({"status": "active"}))

        # Calculate fare
        current_hour = datetime.now().hour
        is_peak = fare_calculator.is_peak_hour(current_hour)
        fare_info = fare_calculator.calculate_fare(distance_km, is_peak)

        # Format response with bus numbers and route details
        results = []
        for route in all_routes:
            # Get buses assigned to this route
            assigned_buses = route.get("assigned_buses", [])
            bus_numbers = []

            for bus_id in assigned_buses:
                bus = buses_collection.find_one({"bus_id": bus_id})
                if bus:
                    bus_numbers.append(bus.get("bus_number", f"Bus {bus_id}"))

            # If no buses found in assigned_buses, try finding by route_id
            if not bus_numbers:
                buses_on_route = list(buses_collection.find({"assigned_route_id": route["route_id"]}))
                bus_numbers = [b.get("bus_number", f"Bus {b.get('bus_id', 'Unknown')}") for b in buses_on_route]

            # Get schedule for this route
            schedule = schedules_collection.find_one({"route_id": route["route_id"], "active": True})

            # Calculate ETA
            route_duration = route.get("estimated_duration_min", duration_min)
            eta_min = route_duration
            frequency_min = 10  # Default
            departure_times = []

            if schedule:
                frequency_min = schedule.get("frequency_min", 10)
                # Estimated wait time is half the frequency on average
                eta_min += frequency_min / 2
                departure_times = schedule.get("departure_times", [])

            # Get route details
            source_name = route.get("source_name", "Unknown")
            dest_name = route.get("dest_name", "Unknown")
            waypoints = route.get("waypoints", [])

            results.append({
                "route_id": route["route_id"],
                "route_name": route.get("name", f"{source_name} → {dest_name}"),
                "source_name": source_name,
                "dest_name": dest_name,
                "bus_numbers": bus_numbers,  # List of bus numbers on this route
                "distance_km": route.get("total_distance_km", distance_km),
                "eta_min": round(eta_min, 1),
                "fare": fare_info["final_fare"],
                "frequency_min": frequency_min,
                "is_peak_hour": is_peak,
                "waypoints": waypoints,  # Route path for map display
                "departure_times": departure_times[:5] if departure_times else [],  # Next 5 departures
                "total_buses": len(bus_numbers)
            })

        return {
            "source": {"lat": request.source_lat, "lng": request.source_lng},
            "destination": {"lat": request.dest_lat, "lng": request.dest_lng},
            "distance_km": round(distance_km, 2),
            "available_routes": results,
            "fare_details": fare_info,
            "total_routes_found": len(results)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching buses: {str(e)}"
        )


@router.get("/recommendations")
async def get_recommendations(current_user: Dict = Depends(require_passenger)):
    """
    Get personalized bus recommendations based on travel history
    """
    try:
        passenger_id = current_user.get("sub")
        
        recommendations = gemini_recommender.get_personalized_recommendations(passenger_id)
        patterns = gemini_recommender.analyze_travel_patterns(passenger_id)
        
        return {
            "recommendations": recommendations,
            "travel_patterns": patterns,
            "current_time": datetime.now().strftime("%H:%M"),
            "day": datetime.now().strftime("%A")
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting recommendations: {str(e)}"
        )


@router.get("/history")
async def get_travel_history(current_user: Dict = Depends(require_passenger)):
    """Get passenger travel history"""
    try:
        passenger_id = current_user.get("sub")
        
        history_collection = mongodb.get_collection("travel_history")
        history = list(history_collection.find(
            {"passenger_id": passenger_id}
        ).sort("timestamp", -1).limit(50))
        
        # Convert ObjectId to string
        for record in history:
            record["_id"] = str(record["_id"])
            if isinstance(record.get("timestamp"), datetime):
                record["timestamp"] = record["timestamp"].isoformat()
        
        return {
            "total": len(history),
            "history": history
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching history: {str(e)}"
        )


@router.post("/history/log")
async def log_travel(travel_data: Dict, current_user: Dict = Depends(require_passenger)):
    """Log a travel/trip"""
    try:
        passenger_id = current_user.get("sub")
        
        now = datetime.now()
        
        history_record = {
            "passenger_id": passenger_id,
            "route_id": travel_data.get("route_id"),
            "source_stop_id": travel_data.get("source_stop_id", ""),
            "dest_stop_id": travel_data.get("dest_stop_id", ""),
            "travel_time": now.strftime("%H:%M"),
            "day_of_week": now.strftime("%A"),
            "timestamp": now
        }
        
        history_collection = mongodb.get_collection("travel_history")
        result = history_collection.insert_one(history_record)
        
        return {
            "message": "Travel logged successfully",
            "history_id": str(result.inserted_id)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error logging travel: {str(e)}"
        )


@router.post("/fare/calculate")
async def calculate_fare(request: FareRequest):
    """Calculate fare for a distance"""
    try:
        fare_info = fare_calculator.calculate_fare(
            request.distance_km,
            request.is_peak_hour
        )
        
        return fare_info
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating fare: {str(e)}"
        )


@router.get("/fare/route/{route_id}")
async def get_route_fare(route_id: str, is_peak_hour: bool = False):
    """Get fare for a specific route"""
    try:
        fare_info = fare_calculator.estimate_fare_for_route(route_id, is_peak_hour)

        if not fare_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route not found"
            )

        return fare_info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting route fare: {str(e)}"
        )


@router.post("/find-connections")
async def find_interconnected_routes(request: InterconnectedRouteRequest, current_user: Dict = Depends(get_current_user)):
    """
    Find interconnected routes for multi-leg journeys
    Remembers passenger's current trip and suggests connecting routes
    """
    try:
        passenger_id = current_user.get("sub") or current_user.get("email")

        # Check if passenger has an active trip
        current_trips_collection = mongodb.get_collection("current_trips")
        active_trip = current_trips_collection.find_one({
            "passenger_id": passenger_id,
            "is_active": True
        })

        # Find interconnected routes
        route_options = route_connector.find_interconnected_routes(
            current_lat=request.current_lat,
            current_lng=request.current_lng,
            final_dest_lat=request.final_dest_lat,
            final_dest_lng=request.final_dest_lng,
            max_transfer_distance_km=0.5
        )

        # Calculate fares for each option
        for option in route_options:
            total_fare = 0.0
            for leg in option.get('legs', []):
                distance_km = leg.get('distance_km', 0)
                # Assume peak hour for now - can be enhanced
                fare_info = fare_calculator.calculate_fare(distance_km, is_peak_hour=False)
                leg['fare'] = fare_info['final_fare']
                total_fare += fare_info['final_fare']

            option['total_fare'] = round(total_fare, 2)

        # Convert ObjectId and datetime to string for JSON serialization
        if active_trip:
            if '_id' in active_trip:
                active_trip['_id'] = str(active_trip['_id'])
            if isinstance(active_trip.get("started_at"), datetime):
                active_trip["started_at"] = active_trip["started_at"].isoformat()

        return {
            "passenger_id": passenger_id,
            "has_active_trip": active_trip is not None,
            "active_trip": active_trip if active_trip else None,
            "route_options": route_options,
            "total_options": len(route_options)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding connections: {str(e)}"
        )


@router.post("/trip/start")
async def start_trip(
    source_name: str,
    source_lat: float,
    source_lng: float,
    dest_name: str,
    dest_lat: float,
    dest_lng: float,
    route_id: str,
    bus_number: str,
    current_user: Dict = Depends(get_current_user)
):
    """Start a new trip for passenger"""
    try:
        passenger_id = current_user.get("sub") or current_user.get("email")
        current_trips_collection = mongodb.get_collection("current_trips")

        # End any existing active trips
        current_trips_collection.update_many(
            {"passenger_id": passenger_id, "is_active": True},
            {"$set": {"is_active": False}}
        )

        # Create new trip
        trip = {
            "passenger_id": passenger_id,
            "current_route_id": route_id,
            "current_bus_number": bus_number,
            "source_name": source_name,
            "source_lat": source_lat,
            "source_lng": source_lng,
            "final_destination_name": dest_name,
            "final_dest_lat": dest_lat,
            "final_dest_lng": dest_lng,
            "current_location_name": source_name,
            "current_lat": source_lat,
            "current_lng": source_lng,
            "completed_legs": [],
            "total_fare_so_far": 0.0,
            "started_at": datetime.utcnow(),
            "is_active": True
        }

        result = current_trips_collection.insert_one(trip)
        trip["_id"] = str(result.inserted_id)

        # Convert datetime to string for JSON serialization
        if isinstance(trip.get("started_at"), datetime):
            trip["started_at"] = trip["started_at"].isoformat()

        return {
            "message": "Trip started successfully",
            "trip": trip
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting trip: {str(e)}"
        )


@router.post("/trip/switch-route")
async def switch_route(
    new_route_id: str,
    new_bus_number: str,
    boarding_location_name: str,
    boarding_lat: float,
    boarding_lng: float,
    current_user: Dict = Depends(get_current_user)
):
    """Switch to a different route mid-journey"""
    try:
        passenger_id = current_user.get("sub") or current_user.get("email")
        current_trips_collection = mongodb.get_collection("current_trips")
        routes_collection = mongodb.get_collection("routes")

        # Get active trip
        active_trip = current_trips_collection.find_one({
            "passenger_id": passenger_id,
            "is_active": True
        })

        if not active_trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active trip found"
            )

        # Get previous route info
        prev_route = routes_collection.find_one({"route_id": active_trip["current_route_id"]})

        # Calculate fare for completed leg
        from math import radians, sin, cos, sqrt, atan2

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            return R * c

        leg_distance = haversine(
            active_trip["current_lat"],
            active_trip["current_lng"],
            boarding_lat,
            boarding_lng
        )

        fare_info = fare_calculator.calculate_fare(leg_distance, is_peak_hour=False)

        # Add completed leg
        completed_leg = {
            "route_id": active_trip["current_route_id"],
            "route_name": prev_route.get("name", "Unknown") if prev_route else "Unknown",
            "bus_number": active_trip["current_bus_number"],
            "source_name": active_trip["current_location_name"],
            "source_lat": active_trip["current_lat"],
            "source_lng": active_trip["current_lng"],
            "dest_name": boarding_location_name,
            "dest_lat": boarding_lat,
            "dest_lng": boarding_lng,
            "distance_km": round(leg_distance, 2),
            "fare": fare_info["final_fare"],
            "boarding_time": datetime.utcnow().strftime("%H:%M")
        }

        # Update trip
        updated_legs = active_trip.get("completed_legs", [])
        updated_legs.append(completed_leg)

        new_total_fare = active_trip.get("total_fare_so_far", 0.0) + fare_info["final_fare"]

        current_trips_collection.update_one(
            {"_id": active_trip["_id"]},
            {"$set": {
                "current_route_id": new_route_id,
                "current_bus_number": new_bus_number,
                "current_location_name": boarding_location_name,
                "current_lat": boarding_lat,
                "current_lng": boarding_lng,
                "completed_legs": updated_legs,
                "total_fare_so_far": new_total_fare
            }}
        )

        return {
            "message": "Route switched successfully",
            "completed_leg": completed_leg,
            "new_route_id": new_route_id,
            "total_fare_so_far": round(new_total_fare, 2),
            "total_legs_completed": len(updated_legs)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error switching route: {str(e)}"
        )


@router.post("/trip/complete")
async def complete_trip(current_user: Dict = Depends(get_current_user)):
    """Complete the current trip"""
    try:
        passenger_id = current_user.get("sub") or current_user.get("email")
        current_trips_collection = mongodb.get_collection("current_trips")
        travel_history_collection = mongodb.get_collection("travel_history")

        # Get active trip
        active_trip = current_trips_collection.find_one({
            "passenger_id": passenger_id,
            "is_active": True
        })

        if not active_trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active trip found"
            )

        # Calculate final leg
        from math import radians, sin, cos, sqrt, atan2

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            return R * c

        final_leg_distance = haversine(
            active_trip["current_lat"],
            active_trip["current_lng"],
            active_trip["final_dest_lat"],
            active_trip["final_dest_lng"]
        )

        final_fare_info = fare_calculator.calculate_fare(final_leg_distance, is_peak_hour=False)
        total_fare = active_trip.get("total_fare_so_far", 0.0) + final_fare_info["final_fare"]

        # Save to travel history
        history = {
            "passenger_id": passenger_id,
            "route_id": active_trip["current_route_id"],
            "source_stop_id": "custom",
            "dest_stop_id": "custom",
            "source_name": active_trip["source_name"],
            "dest_name": active_trip["final_destination_name"],
            "source_lat": active_trip["source_lat"],
            "source_lng": active_trip["source_lng"],
            "dest_lat": active_trip["final_dest_lat"],
            "dest_lng": active_trip["final_dest_lng"],
            "travel_time": str(datetime.utcnow() - active_trip["started_at"]),
            "day_of_week": datetime.utcnow().strftime("%A"),
            "trip_legs": active_trip.get("completed_legs", []),
            "total_fare": round(total_fare, 2),
            "is_multi_leg": len(active_trip.get("completed_legs", [])) > 0,
            "timestamp": datetime.utcnow()
        }

        result = travel_history_collection.insert_one(history)

        # Convert ObjectId to string for JSON serialization
        history['_id'] = str(result.inserted_id)
        if isinstance(history.get("timestamp"), datetime):
            history["timestamp"] = history["timestamp"].isoformat()

        # Mark trip as complete
        current_trips_collection.update_one(
            {"_id": active_trip["_id"]},
            {"$set": {"is_active": False}}
        )

        return {
            "message": "Trip completed successfully",
            "total_fare": round(total_fare, 2),
            "total_legs": len(active_trip.get("completed_legs", [])) + 1,
            "is_multi_leg": len(active_trip.get("completed_legs", [])) > 0,
            "trip_summary": history
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing trip: {str(e)}"
        )

