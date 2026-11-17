
from fastapi import FastAPI

from backend.app.routers import tickets

app = FastAPI(
    title="AI Employee Helpdesk",
    description="An AI-powered employee IT support ticket management system",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Welcome to AI Employee Helpdesk API",
        "status": "Running successfully"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# Register ticket APIs
app.include_router(tickets.router)


