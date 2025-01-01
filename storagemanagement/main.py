from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# MongoDB setup
client = MongoClient("mongodb+srv://msamibese22seecs:i9UvBXQv6HsdOqvY@cluster0.ozyev.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["StorageDatabase"]
storage_collection = db["storage"]

# Logging setup
log_db = client["LogDatabase"]
log_collection = log_db["logs"]

MAX_STORAGE_MB = 50

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
@app.get("/storage/{username}")
def get_storage(username: str):
    """Retrieve storage usage for a specific user."""
    user_storage = storage_collection.find_one({"username": username})
    if not user_storage:
        storage_collection.insert_one({"username": username, "used_storage": 0})
        save_log("StorageMgmtServ", "Storage Retrieved", {"username": username, "used_storage": 0})
        return {"used_storage": 0, "max_storage": MAX_STORAGE_MB}
    save_log("StorageMgmtServ", "Storage Retrieved", {"username": username, "used_storage": user_storage["used_storage"]})
    return {"used_storage": user_storage["used_storage"], "max_storage": MAX_STORAGE_MB}

@app.post("/storage/upload/{username}/{size_mb}")
def upload(username: str, size_mb: int):
    """Log storage usage for a specific user."""
    user_storage = storage_collection.find_one({"username": username})
    if not user_storage:
        storage_collection.insert_one({"username": username, "used_storage": 0})
        user_storage = {"username": username, "used_storage": 0}

    if user_storage["used_storage"] + size_mb > MAX_STORAGE_MB:
        save_log("StorageMgmtServ", "Storage Limit Exceeded", {"username": username, "attempted_upload": size_mb, "current_usage": user_storage["used_storage"]})
        raise HTTPException(status_code=400, detail="Storage limit exceeded")

    storage_collection.update_one({"username": username}, {"$inc": {"used_storage": size_mb}})
    save_log("StorageMgmtServ", "Storage Used", {"username": username, "new_usage": user_storage["used_storage"] + size_mb})
    return {"message": "Upload successful"}
