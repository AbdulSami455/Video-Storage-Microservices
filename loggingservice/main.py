from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from typing import List
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

client = MongoClient("mongodb+srv://msamibese22seecs:i9UvBXQv6HsdOqvY@cluster0.ozyev.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
log_db = client["LogDatabase"]
log_collection = log_db["logs"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (or specify your frontend origin)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

@app.get("/logging/logs", response_model=List[dict])
def get_logs(service: str = None, event: str = None) -> List[dict]:
    """
    Retrieve logs from the LogDatabase.
    - Optionally filter by service name and event type.
    """
    try:
        query = {}
        if service:
            query["service"] = service
        if event:
            query["event"] = event

        logs = list(log_collection.find(query, {"_id": 0}))
        return logs  
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")
