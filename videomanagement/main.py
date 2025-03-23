from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from pymongo import MongoClient
import boto3
from botocore.exceptions import NoCredentialsError
from typing import List, Optional
import datetime
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, S3_BUCKET_NAME]):
    raise EnvironmentError("Missing one or more required environment variables")

app = FastAPI()

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

client = MongoClient("")
log_db = client["LogDatabase"]
log_collection = log_db["logs"]

def save_log(service_name, event, details):
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
@app.post("/video/upload-video/{username}")
def upload_video(username: str, file: UploadFile = File(...)):
    """
    Upload a video to S3 under the user's folder and make it publicly accessible via bucket policy.
    """
    try:
        s3_key = f"{username}/{file.filename}"

        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET_NAME,
            s3_key
        )

        file_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"

        save_log("ViewGeneratorServ", "Video Uploaded", {"username": username, "file_url": file_url})

        return {"message": "Video uploaded successfully", "file_url": file_url}
    except NoCredentialsError:
        save_log("ViewGeneratorServ", "Error", {"error": "Invalid AWS credentials"})
        raise HTTPException(status_code=500, detail="Invalid AWS credentials")
    
    except Exception as e:
        save_log("ViewGeneratorServ", "Error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Error uploading video: {str(e)}")

@app.get("/video/list-videos/{username}", response_model=List[str])
def list_videos(username: str) -> List[str]:
    """
    List all videos uploaded by a specific user.
    """
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=f"{username}/")

        if "Contents" not in response:
            save_log("ViewGeneratorServ", "List Videos", {"username": username, "videos": []})
            return []

        video_urls = [
            f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{obj['Key']}"
            for obj in response["Contents"]
        ]

        save_log("ViewGeneratorServ", "List Videos", {"username": username, "videos": video_urls})

        return video_urls  
    except Exception as e:
        save_log("ViewGeneratorServ", "Error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Error listing videos: {str(e)}")

@app.delete("/video/delete-video/{username}/{filename}")
def delete_video(username: str, filename: str):
    """
    Delete a specific video uploaded by the user.
    """
    try:
        s3_key = f"{username}/{filename}"

        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)

        save_log("ViewGeneratorServ", "Video Deleted", {"username": username, "file": filename})

        return {"message": f"Video '{filename}' deleted successfully."}
    except Exception as e:
        save_log("ViewGeneratorServ", "Error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Error deleting video: {str(e)}")

@app.get("/video/filter-videos/{username}", response_model=List[str])
def filter_videos(username: str, prefix: Optional[str] = Query(None), suffix: Optional[str] = Query(None)):
    """
    Filter videos by prefix or suffix for a specific user.
    """
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=f"{username}/")

        if "Contents" not in response:
            save_log("ViewGeneratorServ", "Filter Videos", {"username": username, "filter": {"prefix": prefix, "suffix": suffix}, "videos": []})
            return []

        # Filter videos by prefix and suffix
        video_urls = [
            f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{obj['Key']}"
            for obj in response["Contents"]
            if (not prefix or obj["Key"].startswith(f"{username}/{prefix}")) and 
               (not suffix or obj["Key"].endswith(suffix))
        ]

        save_log("ViewGeneratorServ", "Filter Videos", {"username": username, "filter": {"prefix": prefix, "suffix": suffix}, "videos": video_urls})

        return video_urls
    except Exception as e:
        save_log("ViewGeneratorServ", "Error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Error filtering videos: {str(e)}")
