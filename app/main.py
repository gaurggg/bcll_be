from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.mongodb import mongodb
from app.api import auth, admin_routes, passenger_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Bhopal Bus POC API...")
    mongodb.connect()
    yield
    # Shutdown
    print("Shutting down...")
    mongodb.close()


app = FastAPI(
    title="Bhopal Bus POC API",
    description="AI-powered bus routing and scheduling system for Bhopal",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(admin_routes.router)
app.include_router(passenger_routes.router)


@app.get("/")
async def root():
    return {
        "message": "Bhopal Bus POC API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected" if mongodb.db is not None else "disconnected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

