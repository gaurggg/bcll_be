# Bhopal Bus POC - AI-Powered Bus Routing System

A Proof of Concept for an intelligent bus routing and scheduling system for Bhopal, MP, India. This system uses AI (Gemini) and Dijkstra's algorithm to optimize bus routes, predict scheduling needs, and provide personalized recommendations to passengers.

## Features

### Admin Portal
- **AI-Assisted Route Planning**: Use Dijkstra algorithm + Gemini AI to get top 5 optimized bus routes
- **Smart Scheduling**: AI predicts optimal bus frequency and fleet size based on traffic and demand
- **Route Management**: Create, update, and manage bus routes
- **Schedule Management**: Create and manage bus schedules for different peak hours

### Passenger Portal
- **Bus Search**: Find buses between any two locations with ETA and fare
- **Fare Calculator**: Distance-based fare calculation with peak-hour pricing
- **Travel History**: Track all past trips
- **Personalized Recommendations**: AI suggests buses based on travel patterns

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: MongoDB (Local)
- **External APIs**:
  - Google Maps Platform (Directions, Distance Matrix, Geocoding)
  - Gemini AI (Route optimization, scheduling, recommendations)
- **Algorithm**: Dijkstra for optimal pathfinding
- **Auth**: JWT-based authentication

## Project Structure

```
bcll_be/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration settings
│   ├── api/
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── admin_routes.py    # Admin portal endpoints
│   │   └── passenger_routes.py # Passenger portal endpoints
│   ├── routing/
│   │   ├── graph_builder.py   # Build road network graph
│   │   └── dijkstra.py        # Dijkstra algorithm implementation
│   ├── ai/
│   │   ├── gemini_route_optimizer.py  # AI route ranking
│   │   ├── gemini_scheduler.py        # AI scheduling predictions
│   │   └── gemini_recommender.py      # AI recommendations
│   ├── fares/
│   │   └── fare_calculator.py  # Fare calculation logic
│   ├── db/
│   │   ├── mongodb.py         # MongoDB connection
│   │   └── models.py          # Pydantic models
│   ├── external/
│   │   ├── google_maps_client.py  # Google Maps API wrapper
│   │   └── gemini_client.py       # Gemini AI wrapper
│   └── utils/
│       └── auth_utils.py      # JWT helpers
├── scripts/
│   └── seed_bhopal_data.py    # Seed sample data
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites

- Python 3.8+
- MongoDB (local installation)
- Google Maps API Key (from GCP)
- Gemini API Key

### Setup Steps

1. **Clone the repository**
```bash
cd bcll_be
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up MongoDB**
```bash
# Install MongoDB locally or use Docker
# For Windows: Download from https://www.mongodb.com/try/download/community
# For Docker:
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

4. **Configure environment variables**

Create a `.env` file in the root directory:

```env
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=bcll_poc
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET=your_random_secret_key_min_32_chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
```

5. **Seed sample data**
```bash
python scripts/seed_bhopal_data.py
```

6. **Run the application**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication

#### Admin Login
```http
POST /auth/admin/login
Content-Type: application/json

{
  "email": "admin@bcll.com",
  "password": "admin123"
}
```

#### Passenger Register
```http
POST /auth/passenger/register
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+919876543210",
  "password": "password123"
}
```

#### Passenger Login
```http
POST /auth/passenger/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "password123"
}
```

### Admin Portal (Requires Admin Token)

#### Plan Route (AI-Assisted)
```http
POST /admin/route/plan
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "source_lat": 23.2599,
  "source_lng": 77.4126,
  "dest_lat": 23.2759,
  "dest_lng": 77.4011,
  "peak_hour": "morning"
}
```

Response: Top 5 AI-ranked routes with scores and reasoning

#### Create Route
```http
POST /admin/route/create
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "MP Nagar to BHEL",
  "source_stop_id": "stop_id_1",
  "dest_stop_id": "stop_id_2",
  "distance_km": 15.5,
  "duration_min": 45,
  "gemini_score": 9.2
}
```

#### Create Schedule (AI Predictions)
```http
POST /admin/schedule/create
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "route_id": "R1",
  "peak_hour": "morning"
}
```

Response: AI predicts bus frequency and fleet size needed

#### Get All Routes
```http
GET /admin/routes
Authorization: Bearer <admin_token>
```

#### Get All Schedules
```http
GET /admin/schedules
Authorization: Bearer <admin_token>
```

### Passenger Portal (Requires Passenger Token)

#### Search Buses
```http
POST /passenger/search
Authorization: Bearer <passenger_token>
Content-Type: application/json

{
  "source_lat": 23.2599,
  "source_lng": 77.4126,
  "dest_lat": 23.2759,
  "dest_lng": 77.4011
}
```

Response: Available buses with ETA and fare

#### Get Personalized Recommendations
```http
GET /passenger/recommendations
Authorization: Bearer <passenger_token>
```

Response: AI-powered bus recommendations based on travel history

#### Get Travel History
```http
GET /passenger/history
Authorization: Bearer <passenger_token>
```

#### Log Travel
```http
POST /passenger/history/log
Authorization: Bearer <passenger_token>
Content-Type: application/json

{
  "route_id": "R1",
  "source_stop_id": "stop_1",
  "dest_stop_id": "stop_2"
}
```

#### Calculate Fare
```http
POST /passenger/fare/calculate
Content-Type: application/json

{
  "distance_km": 10.5,
  "is_peak_hour": true
}
```

## How It Works

### Route Planning Flow

1. **Admin selects source and destination** on Google Maps
2. **System fetches alternative routes** from Google Maps Directions API
3. **Dijkstra algorithm** processes the road network graph
4. **Google Maps provides traffic data** for each route
5. **Gemini AI analyzes** all routes based on:
   - Distance and duration efficiency
   - Traffic patterns
   - Suitability for bus operations
   - Coverage of major areas
6. **Returns top 5 ranked routes** with scores and reasoning

### Scheduling Flow

1. **Admin selects a route and peak hour**
2. **System retrieves route details** (distance, duration, traffic)
3. **Gemini AI predicts**:
   - Optimal bus frequency (5-10 min for peak, 12-15 min off-peak)
   - Number of buses needed
   - Expected passenger demand
4. **System creates schedule** with AI recommendations

### Passenger Recommendation Flow

1. **System analyzes passenger's travel history**
   - Frequent time slots
   - Common routes
   - Day patterns
2. **Gemini AI identifies patterns**
3. **Provides personalized suggestions** like:
   - "Your usual 8 AM bus to BHEL is arriving in 5 minutes"

## Database Collections

### stops
Stores bus stop information
- name, location (GeoJSON), type (major/regular), avg_dwell_time_s

### buses
Stores bus fleet information
- bus_number, capacity, status

### routes
Stores bus routes
- route_id, name, source/dest, path, distance, duration, AI scores

### schedules
Stores bus schedules
- route_id, bus_id, peak_hour, frequency, suggested_buses_count

### passengers
Stores passenger accounts
- name, email, phone, password_hash

### travel_history
Stores passenger trip history
- passenger_id, route_id, source/dest, travel_time, day_of_week

### fare_config
Stores fare configuration
- distance_slab_km, base_fare_inr, peak_multiplier

## Testing

### Using Swagger UI

1. Go to `http://localhost:8000/docs`
2. Click "Authorize" and enter your JWT token
3. Try out the endpoints

### Using curl

```bash
# Admin login
curl -X POST http://localhost:8000/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bcll.com","password":"admin123"}'

# Use the token from response
TOKEN="your_token_here"

# Plan a route
curl -X POST http://localhost:8000/admin/route/plan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_lat": 23.2599,
    "source_lng": 77.4126,
    "dest_lat": 23.2759,
    "dest_lng": 77.4011
  }'
```

## Configuration

### Peak Hours
- Morning: 8:00 AM - 11:59 AM
- Evening: 6:00 PM - 9:00 PM
- Off-peak: All other times

### Target Headways
- Peak hours: 5-10 minutes
- Off-peak: 12-15 minutes

### Fare Structure
- 0-5 km: ₹10 (₹12 peak)
- 5-10 km: ₹15 (₹18 peak)
- 10-20 km: ₹25 (₹30 peak)
- 20-50 km: ₹40 (₹48 peak)

## Troubleshooting

### MongoDB Connection Error
- Ensure MongoDB is running: `mongo --version`
- Check connection string in `.env`

### Google Maps API Error
- Verify API key is valid
- Enable required APIs in GCP Console:
  - Directions API
  - Distance Matrix API
  - Geocoding API

### Gemini API Error
- Ensure you have a valid Gemini API key
- Check API quota limits

## Future Enhancements

- Real-time bus tracking with GPS
- Live traffic-based dynamic routing
- Mobile apps (iOS/Android)
- Web dashboard for admin and passengers
- Multi-city support
- Advanced analytics and reporting
- Integration with payment systems
- QR code-based ticketing

## License

This is a POC project for demonstration purposes.

## Contact

For questions or support, contact the development team.

