import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base
from app.api.v1 import (
    auth,
    users,
    departments,
    employees,
    categories,
    vendors,
    assets,
    assignments,
    software,
    maintenance,
    warranties,
    dashboard,
    audit,
    notifications,
)

# Ensure database tables exist if running locally
Base.metadata.create_all(bind=engine)

# Ensure media directory exists
os.makedirs(settings.MEDIA_DIR, exist_ok=True)
os.makedirs(settings.QR_DIR, exist_ok=True)
os.makedirs(settings.REPORTS_DIR, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise IT Asset Management Platform API - Inventory, Lifecycle, Approvals, Software Licenses, and Maintenance.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount media directory for QR codes & reports
app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")

# Include Routers
v1 = settings.API_V1_STR
app.include_router(auth.router, prefix=v1)
app.include_router(users.router, prefix=v1)
app.include_router(departments.router, prefix=v1)
app.include_router(employees.router, prefix=v1)
app.include_router(categories.router, prefix=v1)
app.include_router(vendors.router, prefix=v1)
app.include_router(assets.router, prefix=v1)
app.include_router(assignments.router, prefix=v1)
app.include_router(software.router, prefix=v1)
app.include_router(maintenance.router, prefix=v1)
app.include_router(warranties.router, prefix=v1)
app.include_router(dashboard.router, prefix=v1)
app.include_router(audit.router, prefix=v1)
app.include_router(notifications.router, prefix=v1)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API. Access documentation at /docs",
        "version": settings.VERSION
    }
