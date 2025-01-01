from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import bcrypt
import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# MongoDB setup
client = MongoClient("mongodb+srv://msamibese22seecs:i9UvBXQv6HsdOqvY@cluster0.ozyev.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["UserDatabase"]
user_collection = db["users"]

# Logging setup
log_db = client["LogDatabase"]
log_collection = log_db["logs"]

def save_log(service_name, event, details):
    """Save log entry to the LogDatabase."""
    log_entry = {
        "service": service_name,
        "event": event,
        "details": details,
        "timestamp": datetime.datetime.utcnow()
    }
    log_collection.insert_one(log_entry)

class User(BaseModel):
    username: str
    password: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (or specify your frontend origin)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/user/register")
def register(user: User):
    """Register a new user."""
    if user_collection.find_one({"username": user.username}):
        save_log("UserAccMgmtServ", "Registration Failed", {"username": user.username, "reason": "User already exists"})
        raise HTTPException(status_code=400, detail="User already exists")
    hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    user_collection.insert_one({"username": user.username, "password": hashed})
    save_log("UserAccMgmtServ", "User Registered", {"username": user.username})
    return {"message": "User registered successfully"}

@app.post("/user/login")
def login(user: User):
    """Authenticate a user."""
    user_record = user_collection.find_one({"username": user.username})
    if not user_record or not bcrypt.checkpw(user.password.encode(), user_record["password"]):
        save_log("UserAccMgmtServ", "Login Failed", {"username": user.username, "reason": "Invalid credentials"})
        raise HTTPException(status_code=400, detail="Invalid username or password")
    save_log("UserAccMgmtServ", "Login Successful", {"username": user.username})
    return {"message": "Login successful"}
