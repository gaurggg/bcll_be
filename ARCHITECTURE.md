# System Architecture - Bhopal Bus POC

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  Admin Portal              │         Passenger Portal            │
│  - Route Planning          │         - Bus Search                │
│  - Scheduling              │         - Fare Calculation          │
│  - Management              │         - Recommendations           │
└────────────┬────────────────┴────────────┬────────────────────────┘
             │                             │
             │         HTTP/REST           │
             │         (JWT Auth)          │
             │                             │
┌────────────┴─────────────────────────────┴────────────────────────┐
│                      FASTAPI BACKEND                               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │   API Routes     │  │   Auth Layer     │  │   Middleware    │ │
│  │  - Admin APIs    │  │   - JWT Tokens   │  │   - CORS        │ │
│  │  - Passenger APIs│  │   - Role-based   │  │   - Logging     │ │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    BUSINESS LOGIC LAYER                      │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │                                                              │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │  Routing    │  │   AI Layer  │  │   Fare Calculator   │ │ │
│  │  │  - Dijkstra │  │  - Gemini   │  │  - Distance-based   │ │ │
│  │  │  - Graph    │  │  - Optimize │  │  - Peak pricing     │ │ │
│  │  │  - Pathfind │  │  - Predict  │  │                     │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
             │                             │
             │                             │
┌────────────┴─────────────────────────────┴────────────────────────┐
│                      DATA & EXTERNAL LAYER                         │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐│
│  │   MongoDB    │  │  Google Maps │  │      Gemini AI           ││
│  │  - Stops     │  │  - Directions│  │  - Route Ranking         ││
│  │  - Routes    │  │  - Distance  │  │  - Schedule Prediction   ││
│  │  - Schedules │  │  - Traffic   │  │  - Recommendations       ││
│  │  - History   │  │  - Geocoding │  │                          ││
│  └──────────────┘  └──────────────┘  └──────────────────────────┘│
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. API Layer (`app/api/`)

```
app/api/
├── auth.py
│   ├── POST /auth/admin/login
│   ├── POST /auth/passenger/register
│   └── POST /auth/passenger/login
│
├── admin_routes.py
│   ├── POST /admin/route/plan           [AI Route Planning]
│   ├── POST /admin/route/create         [Create Route]
│   ├── POST /admin/schedule/create      [AI Scheduling]
│   ├── GET  /admin/routes               [List Routes]
│   ├── GET  /admin/routes/{id}          [Get Route]
│   ├── PUT  /admin/route/{id}           [Update Route]
│   ├── DELETE /admin/route/{id}         [Delete Route]
│   └── GET  /admin/schedules            [List Schedules]
│
└── passenger_routes.py
    ├── POST /passenger/search           [Bus Search + ETA]
    ├── GET  /passenger/recommendations  [AI Recommendations]
    ├── GET  /passenger/history          [Travel History]
    ├── POST /passenger/history/log      [Log Trip]
    ├── POST /passenger/fare/calculate   [Calculate Fare]
    └── GET  /passenger/fare/route/{id}  [Route Fare]
```

### 2. Routing Engine (`app/routing/`)

```
┌──────────────────────────────────────────────────────┐
│              ROUTING ENGINE FLOW                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  1. graph_builder.py                                │
│     ├─ Fetch directions from Google Maps           │
│     ├─ Build weighted directed graph                │
│     ├─ Nodes: Intersections/Waypoints               │
│     └─ Edges: Road segments (distance, duration)    │
│                                                      │
│  2. dijkstra.py                                     │
│     ├─ Find shortest path (Dijkstra)                │
│     ├─ Find k-shortest paths (Yen's algorithm)      │
│     ├─ Calculate path costs                         │
│     └─ Return path details                          │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 3. AI Integration (`app/ai/`)

```
┌──────────────────────────────────────────────────────┐
│                  AI WORKFLOW                         │
├──────────────────────────────────────────────────────┤
│                                                      │
│  gemini_route_optimizer.py                          │
│  ┌────────────────────────────────────────┐         │
│  │ Input: Multiple route alternatives     │         │
│  │ ├─ Distance, duration                  │         │
│  │ ├─ Traffic data                        │         │
│  │ ├─ Number of segments                  │         │
│  │                                        │         │
│  │ Process: Gemini AI analysis            │         │
│  │ ├─ Traffic efficiency                  │         │
│  │ ├─ Route complexity                    │         │
│  │ ├─ Coverage potential                  │         │
│  │ ├─ Bus operation suitability           │         │
│  │                                        │         │
│  │ Output: Ranked routes                  │         │
│  │ ├─ Score (0-10)                        │         │
│  │ ├─ Traffic score                       │         │
│  │ └─ Reasoning                           │         │
│  └────────────────────────────────────────┘         │
│                                                      │
│  gemini_scheduler.py                                │
│  ┌────────────────────────────────────────┐         │
│  │ Input: Route + Peak hour               │         │
│  │                                        │         │
│  │ Process: AI prediction                 │         │
│  │ ├─ Analyze route duration              │         │
│  │ ├─ Consider traffic patterns           │         │
│  │ ├─ Estimate demand                     │         │
│  │                                        │         │
│  │ Output: Schedule recommendations       │         │
│  │ ├─ Bus frequency (minutes)             │         │
│  │ ├─ Number of buses needed              │         │
│  │ └─ Expected passengers/hour            │         │
│  └────────────────────────────────────────┘         │
│                                                      │
│  gemini_recommender.py                              │
│  ┌────────────────────────────────────────┐         │
│  │ Input: Travel history                  │         │
│  │                                        │         │
│  │ Process: Pattern recognition           │         │
│  │ ├─ Frequent routes                     │         │
│  │ ├─ Time patterns                       │         │
│  │ ├─ Day patterns                        │         │
│  │                                        │         │
│  │ Output: Personalized suggestions       │         │
│  │ ├─ Recommended routes                  │         │
│  │ ├─ Confidence score                    │         │
│  │ └─ Reasoning                           │         │
│  └────────────────────────────────────────┘         │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 4. External Services (`app/external/`)

```
┌──────────────────────────────────────────────────────┐
│           EXTERNAL SERVICE INTEGRATION               │
├──────────────────────────────────────────────────────┤
│                                                      │
│  google_maps_client.py                              │
│  ├─ get_directions()      → Route alternatives      │
│  ├─ get_distance_matrix() → Distance + ETA          │
│  ├─ geocode_address()     → Address → Coordinates   │
│  ├─ reverse_geocode()     → Coordinates → Address   │
│  └─ get_traffic_info()    → Traffic conditions      │
│                                                      │
│  gemini_client.py                                   │
│  ├─ generate_content()    → AI text generation      │
│  ├─ rank_routes()         → Route analysis          │
│  ├─ predict_schedule()    → Bus scheduling          │
│  └─ recommend_buses()     → Personalized recs       │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 5. Data Models (`app/db/`)

```
MongoDB Collections:

stops
├─ name: string
├─ location: GeoJSON Point
├─ type: "major" | "regular"
└─ avg_dwell_time_s: int

buses
├─ bus_number: string
├─ capacity: int
└─ status: "active" | "inactive"

routes
├─ route_id: string
├─ name: string
├─ source_stop_id: string
├─ dest_stop_id: string
├─ path: [PathStop]
├─ total_distance_km: float
├─ estimated_duration_min: int
├─ gemini_score: float
├─ traffic_score: float
├─ created_by: string
└─ created_at: datetime

schedules
├─ route_id: string
├─ bus_id: string
├─ peak_hour: "morning" | "evening" | "off-peak"
├─ start_time: string
├─ frequency_min: int
├─ suggested_buses_count: int
└─ active: bool

passengers
├─ name: string
├─ email: string
├─ phone: string
├─ password_hash: string
└─ created_at: datetime

travel_history
├─ passenger_id: string
├─ route_id: string
├─ source_stop_id: string
├─ dest_stop_id: string
├─ travel_time: string
├─ day_of_week: string
└─ timestamp: datetime

fare_config
├─ distance_slab_km: [float]
├─ base_fare_inr: [float]
└─ peak_multiplier: float
```

## Data Flow Diagrams

### Admin Route Planning Flow

```
┌─────────┐
│  Admin  │
└────┬────┘
     │ 1. Select source/dest on map
     ▼
┌─────────────────────┐
│  POST /admin/route/ │
│       plan          │
└─────────┬───────────┘
          │ 2. Request route alternatives
          ▼
┌─────────────────────┐
│  Google Maps API    │
│  - Get directions   │
│  - Get traffic data │
└─────────┬───────────┘
          │ 3. Return 5 alternatives
          ▼
┌─────────────────────┐
│  Graph Builder      │
│  - Build graph      │
│  - Parse waypoints  │
└─────────┬───────────┘
          │ 4. Graph structure
          ▼
┌─────────────────────┐
│  Dijkstra Algorithm │
│  - Find k-shortest  │
│  - Calculate costs  │
└─────────┬───────────┘
          │ 5. Route candidates
          ▼
┌─────────────────────┐
│  Gemini AI          │
│  - Analyze routes   │
│  - Rank by criteria │
│  - Generate scores  │
└─────────┬───────────┘
          │ 6. Top 5 ranked routes
          ▼
┌─────────────────────┐
│  Response to Admin  │
│  - Routes + scores  │
│  - Reasoning        │
└─────────────────────┘
```

### Passenger Bus Search Flow

```
┌──────────┐
│Passenger │
└────┬─────┘
     │ 1. Enter source/dest
     ▼
┌─────────────────────┐
│POST /passenger/     │
│      search         │
└─────────┬───────────┘
          │ 2. Calculate distance
          ▼
┌─────────────────────┐
│ Google Distance     │
│ Matrix API          │
│ - Distance          │
│ - Duration in traffic│
└─────────┬───────────┘
          │ 3. Distance + duration
          ▼
┌─────────────────────┐
│ Find Matching Routes│
│ - Query MongoDB     │
│ - Filter by area    │
└─────────┬───────────┘
          │ 4. Available routes
          ▼
┌─────────────────────┐
│ Calculate Fare      │
│ - Distance slabs    │
│ - Peak multiplier   │
└─────────┬───────────┘
          │ 5. Fare details
          ▼
┌─────────────────────┐
│ Calculate ETA       │
│ - Duration + wait   │
│ - Schedule frequency│
└─────────┬───────────┘
          │ 6. Complete info
          ▼
┌─────────────────────┐
│Response to Passenger│
│ - Routes + ETA      │
│ - Fare              │
└─────────────────────┘
```

## Security Architecture

```
┌──────────────────────────────────────────────┐
│            SECURITY LAYERS                   │
├──────────────────────────────────────────────┤
│                                              │
│  1. Authentication Layer                     │
│     ├─ JWT Token (HS256)                     │
│     ├─ 24-hour expiration                    │
│     └─ Secure token validation               │
│                                              │
│  2. Authorization Layer                      │
│     ├─ Role-based access control             │
│     ├─ Admin vs Passenger roles              │
│     └─ Endpoint-level protection             │
│                                              │
│  3. Data Protection                          │
│     ├─ Password hashing (bcrypt)             │
│     ├─ Environment variables for secrets     │
│     └─ No sensitive data in logs             │
│                                              │
│  4. API Security                             │
│     ├─ CORS middleware                       │
│     ├─ Input validation (Pydantic)           │
│     └─ Error handling (no info leakage)      │
│                                              │
└──────────────────────────────────────────────┘
```

## Scalability Design

```
Current POC:
- Single server
- Local MongoDB
- Synchronous API calls

Production Ready:
┌────────────────────────────────────────┐
│         Load Balancer (nginx)          │
└─────────────┬──────────────────────────┘
              │
    ┌─────────┴─────────┐
    │         │         │
┌───▼───┐ ┌──▼───┐ ┌───▼───┐
│FastAPI│ │FastAPI│ │FastAPI│  Multiple instances
└───┬───┘ └──┬───┘ └───┬───┘
    │        │         │
    └────────┼─────────┘
             │
    ┌────────▼────────┐
    │  Redis Cache    │  API response caching
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │ MongoDB Cluster │  Replica set
    └─────────────────┘
```

## Deployment Architecture

```
Development (Current):
├─ Local machine
├─ MongoDB local
├─ Python venv
└─ uvicorn --reload

Production (Recommended):
├─ Docker containers
├─ Kubernetes orchestration
├─ MongoDB Atlas (Cloud)
├─ GCP Cloud Run / AWS ECS
├─ CI/CD pipeline (GitHub Actions)
├─ Monitoring (Prometheus + Grafana)
└─ Logging (ELK Stack)
```

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Web Framework** | FastAPI | REST API, async support |
| **Database** | MongoDB | Document storage, GeoJSON |
| **AI Engine** | Google Gemini | Route analysis, predictions |
| **Mapping** | Google Maps | Directions, traffic, distance |
| **Algorithm** | Dijkstra | Optimal pathfinding |
| **Auth** | JWT + bcrypt | Security |
| **Graph Processing** | NetworkX | Graph algorithms |
| **Validation** | Pydantic | Data validation |

---

## Performance Characteristics

- **API Response Time**: <500ms (target)
- **Database Queries**: <100ms (indexed)
- **Google Maps API**: ~200-500ms per call
- **Gemini AI**: ~1-3s per analysis
- **Route Planning**: 3-5s (includes all processing)
- **Bus Search**: <1s (cached results)

---

This architecture is designed for:
✅ Scalability (250-300 buses, expandable to 1000+)
✅ Reliability (proper error handling)
✅ Maintainability (modular design)
✅ Performance (caching, indexing)
✅ Security (JWT, role-based access)

