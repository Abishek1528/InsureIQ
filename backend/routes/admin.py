import os
import shutil
import uuid
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from utils.security import (
    create_access_token, 
    decode_access_token, 
    verify_password, 
    get_password_hash
)
# Assuming these exist in their respective modules based on api.py imports
from ingestion import ingest_policy
from retrieval import list_indexed_policies, delete_policy_from_db

logger = logging.getLogger("AdminRoutes")

router = APIRouter(prefix="/admin", tags=["Admin"])

# Load config from env
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
# In a real app, we would store the hash in DB/env. 
# Here we hash the env password for comparison if we want to follow the "hash" requirement.
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_PASSWORD_HASH = get_password_hash(ADMIN_PASSWORD) if ADMIN_PASSWORD else None

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="admin/login")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# --- Dependency ---

def get_current_admin(token: str = Depends(oauth2_scheme)):
    """
    Reusable dependency to verify admin JWT token.
    """
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if username != ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username

# --- Routes ---

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Admin login endpoint to receive JWT token.
    """
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin credentials not configured in environment"
        )

    if form_data.username != ADMIN_USERNAME or not verify_password(form_data.password, ADMIN_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/upload-policy")
async def upload_policy(
    file: UploadFile = File(...),
    current_admin: str = Depends(get_current_admin)
):
    """
    Protected endpoint to upload insurance policy PDFs.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    file_id = str(uuid.uuid4())[:8]
    safe_filename = f"{file_id}_{file.filename}"
    file_path = DATA_DIR / safe_filename
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved to {file_path}. Starting ingestion...")
        ingest_policy(str(file_path))
        
        return {
            "message": "Policy uploaded and indexed successfully",
            "file_name": safe_filename
        }
    except Exception as e:
        logger.error(f"Upload/Ingestion failed: {str(e)}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to process policy: {str(e)}")

@router.get("/policies")
async def list_policies(current_admin: str = Depends(get_current_admin)):
    """
    Protected endpoint to list all indexed policies.
    """
    try:
        policies = list_indexed_policies()
        return {"policies": policies}
    except Exception as e:
        logger.error(f"Failed to list policies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve policy list")

@router.delete("/delete-policy/{file_name}")
async def delete_policy(
    file_name: str,
    current_admin: str = Depends(get_current_admin)
):
    """
    Protected endpoint to delete a policy.
    """
    try:
        # 1. Delete from ChromaDB
        db_success = delete_policy_from_db(file_name)
        
        # 2. Delete from local storage if needed (logic from api.py was incomplete)
        # We search for the file in DATA_DIR
        file_deleted = False
        for f in DATA_DIR.glob(f"*_{file_name}"):
            f.unlink()
            file_deleted = True
        
        if not db_success and not file_deleted:
            raise HTTPException(status_code=404, detail="Policy not found")

        return {"message": f"Policy {file_name} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete policy: {str(e)}")
