from fastapi import FastAPI
from database import init_db
from routes import router

app = FastAPI(title="Meeting Room Reservation API")

# Initialize database tables
init_db()

# Include routers
app.include_router(router)


@app.get("/")
def root():
    return {"status": "ok", "message": "Meeting Room Reservation API"}