import os
import logging
import shutil
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import existing RAG components
from main import ingest_policy
from retrieval import retrieve_policy_chunks, build_context
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

# Constants
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin-secret-token")

# --- Pydantic Models ---

class UserProfile(BaseModel):
    age: int = Field(..., gt=0, lt=120)
    gender: str = Field(..., min_length=1)
    income: float = Field(..., ge=0)
    dependents: int = Field(..., ge=0)
    medical_history: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)

class ChatQuery(BaseModel):
    query: str = Field(..., min_length=1)

class SourceInfo(BaseModel):
    source: str
    page: int

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]

class RecommendationResponse(BaseModel):
    ranking_table: str
    top_recommendation: str
    detailed_reasoning: str

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
            
        # Parse the structured output from the ranker
        # Note: In a real production app, we might use structured output parsing from LangChain
        # For now, we return the sections as strings
        sections = raw_output.split("###")
        
        ranking_table = ""
        top_rec = ""
        reasoning = ""
        
        for section in sections:
            if "POLICY RANKING TABLE" in section:
                ranking_table = section.strip()
            elif "TOP RECOMMENDATION" in section:
                top_rec = section.strip()
            elif "DETAILED REASONING" in section:
                reasoning = section.strip()
        
        return RecommendationResponse(
            ranking_table=ranking_table,
            top_recommendation=top_rec,
            detailed_reasoning=reasoning
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
        # 1. Retrieve context
        chunks = retrieve_policy_chunks(query_data.query)
        if not chunks:
            return ChatResponse(
                answer="I'm sorry, I couldn't find any information in the policy related to your question.",
                sources=[]
            )
            
        # 2. Build context and call agent logic
        # Re-using the simplified logic from app.py but returning sources
        agent = InsuranceAgent()
        answer = agent.run(query_data.query, {
            "age": 0, "gender": "unknown", "income": 0, 
            "dependents": 0, "medical_history": "unknown", "location": "unknown"
        })
        
        # 3. Extract unique sources
        sources = []
        seen = set()
        for chunk in chunks:
            src_key = f"{chunk['source']}_{chunk['page']}"
            if src_key not in seen:
                sources.append(SourceInfo(source=chunk['source'], page=chunk['page']))
                seen.add(src_key)
                
        return ChatResponse(answer=answer, sources=sources)
        
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "vector_db": os.path.exists("./chroma_db")}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
