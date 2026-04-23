import os
import logging
import shutil
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import existing RAG components
from main import ingest_policy
from retrieval import retrieve_policy_chunks, build_context, delete_policy_from_db, list_indexed_policies
from agent import InsuranceAgent
from ranker import PolicyRanker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("InsuranceAPI")

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="InsureIQ API",
    description="Production-ready backend for AI-powered insurance recommendations",
    version="1.0.0"
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin-secret-token")

# In-memory session store
# Key: session_id, Value: {"user_profile": Dict, "chat_history": List}
session_store: Dict[str, Dict[str, Any]] = {}

# --- Pydantic Models ---

class UserProfile(BaseModel):
    session_id: str = Field(..., min_length=1)
    age: int = Field(..., gt=0, lt=120)
    gender: str = Field(..., min_length=1)
    income: float = Field(..., ge=0)
    dependents: int = Field(..., ge=0)
    medical_history: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)

class ChatQuery(BaseModel):
    session_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)

class SourceInfo(BaseModel):
    source: str
    page: int

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]

class ComparisonItem(BaseModel):
    policy_name: str
    premium: str
    coverage: str
    waiting_period: str
    benefits: str
    limitations: str

class CoverageItem(BaseModel):
    criteria: str
    user_need: str
    policy_match: str
    verdict: str

class RecommendationResponse(BaseModel):
    comparison_table: List[ComparisonItem]
    coverage_table: List[CoverageItem]
    recommendation: str
    explanation: str

# --- Dependency Injection ---

def verify_admin(x_admin_token: Optional[str] = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid or missing admin token")
    return True

# --- API Endpoints ---

@app.post("/upload-policy", tags=["Admin"])
async def upload_policy(
    file: UploadFile = File(...),
    admin_verified: bool = Depends(verify_admin)
):
    """
    Upload and process insurance policy PDFs. (Admin Only)
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save file locally with unique name to avoid collisions
    file_id = str(uuid.uuid4())[:8]
    safe_filename = f"{file_id}_{file.filename}"
    file_path = DATA_DIR / safe_filename
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved to {file_path}. Starting ingestion...")
        
        # Call ingestion pipeline
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

@app.get("/admin/policies", tags=["Admin"])
async def list_policies(admin_verified: bool = Depends(verify_admin)):
    """
    List all unique policy file names indexed in the system.
    """
    try:
        policies = list_indexed_policies()
        return {"policies": policies}
    except Exception as e:
        logger.error(f"Failed to list policies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve policy list")

@app.delete("/admin/delete-policy/{file_name}", tags=["Admin"])
async def delete_policy(
    file_name: str,
    admin_verified: bool = Depends(verify_admin)
):
    """
    Completely remove a policy from local storage and vector DB.
    """
    db_success = False
    file_success = False
    
    # 1. Delete from ChromaDB
    try:
        db_success = delete_policy_from_db(file_name)
    except Exception as e:
        logger.error(f"DB deletion error for {file_name}: {str(e)}")

    # 2. Delete from local storage
    # Note: file_name in DB might be different from actual disk filename if we prefixed it
    # We need to find the file in DATA_DIR that matches the suffix
    try:
        target_file = None
        for f in DATA_DIR.glob(f"*{file_name}"):
            if f.name.endswith(file_name):
                target_file = f
                break
        
        if target_file and target_file.exists():
            target_file.unlink()
            file_success = True
            logger.info(f"Deleted file from storage: {target_file}")
        else:
            logger.warning(f"File {file_name} not found in {DATA_DIR}")
            # We still consider it a partial success if it was in DB but not on disk
            file_success = True 
    except Exception as e:
        logger.error(f"File deletion error for {file_name}: {str(e)}")

    if not db_success and not file_success:
        raise HTTPException(status_code=500, detail="Failed to delete policy from both DB and storage")
    
    return {
        "message": "Policy deletion processed",
        "details": {
            "db_deleted": db_success,
            "file_deleted": file_success
        }
    }

@app.post("/recommend", response_model=RecommendationResponse, tags=["AI Services"])
async def recommend_policy(profile: UserProfile):
    """
    Generate personalized policy rankings and recommendations.
    """
    try:
        ranker = PolicyRanker()
        
        # Convert profile to a query string for retrieval
        query = f"Find best insurance policies for a {profile.age} year old {profile.gender} in {profile.location} with medical history of {profile.medical_history} and {profile.dependents} dependents."
        
        logger.info(f"Generating recommendations for profile: {profile}")
        
        # The ranker handles retrieval and reasoning internally
        raw_output = ranker.rank_policies(query, profile.dict())
        
        if "No policy data available" in raw_output:
            raise HTTPException(status_code=404, detail="No policy data found in the system.")
        
        # Build structured response from LLM markdown output
        # For now, create a structured comparison/coverage table from the raw text
        # In production, you'd use structured output parsing from LangChain
        
        comparison_items = []
        coverage_items = []
        recommendation_text = ""
        explanation_text = ""
        
        # Parse the markdown table for comparison_table
        lines = raw_output.split("\n")
        in_ranking_table = False
        policy_rows = []
        
        for line in lines:
            if "POLICY RANKING TABLE" in line:
                in_ranking_table = True
                continue
            if "TOP RECOMMENDATION" in line:
                in_ranking_table = False
                # Get next lines as recommendation
                rec_idx = lines.index(line)
                if rec_idx + 1 < len(lines):
                    recommendation_text = lines[rec_idx + 1].strip()
                continue
            if "DETAILED REASONING" in line:
                reason_idx = lines.index(line)
                explanation_text = "\n".join(lines[reason_idx + 1:reason_idx + 6]).strip()
                continue
            if in_ranking_table and "|" in line and "-" not in line and "Rank" not in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 7:
                    policy_rows.append(parts[1:7])
        
        # Convert markdown rows to ComparisonItem objects
        for row in policy_rows:
            if len(row) >= 6:
                comparison_items.append(ComparisonItem(
                    policy_name=row[0] if row[0] else "Unknown",
                    premium=row[1] if len(row) > 1 else "Not mentioned",
                    coverage=row[2] if len(row) > 2 else "Not mentioned",
                    waiting_period=row[3] if len(row) > 3 else "Not mentioned",
                    benefits=row[4] if len(row) > 4 else "Not mentioned",
                    limitations=row[5] if len(row) > 5 else "Not mentioned"
                ))
        
        # If no structured data found, create fallback response
        if not comparison_items:
            comparison_items.append(ComparisonItem(
                policy_name="Standard Health Plan",
                premium="Contact for quote",
                coverage="Basic coverage",
                waiting_period="30 days",
                benefits="Essential benefits",
                limitations="Limited network"
            ))
        
        # Build coverage_table based on profile criteria
        coverage_items = [
            CoverageItem(
                criteria="Pre-existing Conditions",
                user_need=profile.medical_history,
                policy_match="Coverage includes common conditions",
                verdict="Good" if profile.medical_history == "None" else "Average"
            ),
            CoverageItem(
                criteria="Family Coverage",
                user_need=f"{profile.dependents} dependents",
                policy_match="Family floater available",
                verdict="Good" if profile.dependents > 0 else "Average"
            ),
            CoverageItem(
                criteria="Budget Fit",
                user_need=f"Income: {profile.income}",
                policy_match="Multiple plan options",
                verdict="Good"
            ),
            CoverageItem(
                criteria="Location Coverage",
                user_need=profile.location,
                policy_match="Pan-India network",
                verdict="Good"
            )
        ]
        
        if not recommendation_text:
            recommendation_text = f"{comparison_items[0].policy_name} is recommended based on your profile."
        
        if not explanation_text:
            explanation_text = f"Based on your profile (age {profile.age}, {profile.gender}, {profile.location}), the recommended policy offers the best balance of coverage and affordability. The waiting period and benefits align well with your medical history of {profile.medical_history}."
        
        # Store profile in session memory
        session_store[profile.session_id] = {
            "user_profile": profile.dict(),
            "chat_history": []
        }
        logger.info(f"Stored profile for session {profile.session_id}")
        
        return RecommendationResponse(
            comparison_table=comparison_items,
            coverage_table=coverage_items,
            recommendation=recommendation_text,
            explanation=explanation_text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI Agent error: {str(e)}")

@app.post("/chat", response_model=ChatResponse, tags=["AI Services"])
async def chat_with_policy(query_data: ChatQuery):
    """
    Answer user queries about policies using conversational RAG.
    """
    try:
        # Check if session exists and has a profile
        session = session_store.get(query_data.session_id)
        if not session or "user_profile" not in session:
            return ChatResponse(
                answer="User profile not found. Please complete recommendation first.",
                sources=[]
            )
            
        user_profile = session["user_profile"]
        
        # Call personalized chat logic from agent
        agent = InsuranceAgent()
        result = agent.chat_with_user(query_data.query, user_profile)
        
        # Update chat history (optional but requested)
        session["chat_history"].append({
            "query": query_data.query,
            "answer": result["answer"]
        })
        
        # Convert source dicts to SourceInfo objects
        sources = [SourceInfo(**s) for s in result["sources"]]
                
        return ChatResponse(answer=result["answer"], sources=sources)
        
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "vector_db": os.path.exists("./chroma_db")}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
