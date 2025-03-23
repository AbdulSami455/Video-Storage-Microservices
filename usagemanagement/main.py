from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# MongoDB setup
client = MongoClient("")
db = client["UsageDatabase"]
bandwidth_collection = db["bandwidth"]

# Logging setup
log_db = client["LogDatabase"]
log_collection = log_db["logs"]

MAX_BANDWIDTH_MB = 100

def save_log(service_name, event, details):
    """Save log entry to the LogDatabase."""
    log_entry = {
        "service": service_name,
        "event": event,
        "details": details,
        "timestamp": datetime.datetime.utcnow()
    }
    log_collection.insert_one(log_entry)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (or specify your frontend origin)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/usage/bandwidth/{username}")
def get_bandwidth(username: str):
    """Retrieve the bandwidth usage for a specific user."""
    user_bandwidth = bandwidth_collection.find_one({"username": username})
    if not user_bandwidth:
        bandwidth_collection.insert_one({"username": username, "used_bandwidth": 0})
        save_log("UsageMntrServ", "Bandwidth Retrieved", {"username": username, "used_bandwidth": 0})
        return {"used_bandwidth": 0, "max_bandwidth": MAX_BANDWIDTH_MB}
    save_log("UsageMntrServ", "Bandwidth Retrieved", {"username": username, "used_bandwidth": user_bandwidth["used_bandwidth"]})
    return {"used_bandwidth": user_bandwidth["used_bandwidth"], "max_bandwidth": MAX_BANDWIDTH_MB}

@app.post("/usage/use_bandwidth/{username}/{size_mb}")
def use_bandwidth(username: str, size_mb: int):
    """Log bandwidth usage for a specific user."""
    user_bandwidth = bandwidth_collection.find_one({"username": username})
    if not user_bandwidth:
        bandwidth_collection.insert_one({"username": username, "used_bandwidth": 0})
        user_bandwidth = {"username": username, "used_bandwidth": 0}

    if user_bandwidth["used_bandwidth"] + size_mb > MAX_BANDWIDTH_MB:
        save_log("UsageMntrServ", "Bandwidth Limit Exceeded", {"username": username, "attempted_usage": size_mb, "current_usage": user_bandwidth["used_bandwidth"]})
        raise HTTPException(status_code=400, detail="Bandwidth limit exceeded")

    bandwidth_collection.update_one({"username": username}, {"$inc": {"used_bandwidth": size_mb}})
    save_log("UsageMntrServ", "Bandwidth Used", {"username": username, "used_bandwidth": user_bandwidth["used_bandwidth"] + size_mb})
    return {"message": "Bandwidth used"}
