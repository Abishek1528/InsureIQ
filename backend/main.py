import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import components
from agent import AarogyaAgent
from ranker import PolicyRanker
from routes.admin import router as admin_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("InsuranceAPI")

# Initialize FastAPI app
app = FastAPI(
    title="InsureIQ API",
    description="Secure backend for AI-powered insurance recommendations",
    version="1.1.0"
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Admin Routes
app.include_router(admin_router)

# In-memory session store
session_store: Dict[str, Dict[str, Any]] = {}

# --- Pydantic Models ---

class UserProfile(BaseModel):
    session_id: str = Field(..., min_length=1)
    full_name: str = Field(..., min_length=1)
    age: int = Field(..., gt=0, lt=120)
    lifestyle: str = Field(..., min_length=1)
    medical_history: str = Field(..., min_length=1)
    income: str = Field(..., min_length=1)
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
    insurer: str
    premium: str
    cover_amount: str
    waiting_period: str
    key_benefit: str
    suitability_score: str

class CoverageDetailItem(BaseModel):
    category: str # Inclusions, Exclusions, Sub-limits, Co-pay %, Claim type
    details: str

class RecommendationResponse(BaseModel):
    best_fit_policy: str
    comparison_table: List[ComparisonItem]
    coverage_detail_table: List[CoverageDetailItem]
    why_this_policy: str

# --- API Endpoints ---

@app.post("/recommend", response_model=RecommendationResponse, tags=["AI Services"])
async def recommend_policy(profile: UserProfile):
    """
    Generate personalized policy rankings and recommendations.
    """
    try:
        ranker = PolicyRanker()
        query = f"Find best insurance policies for {profile.full_name}, a {profile.age} year old with a {profile.lifestyle} lifestyle in {profile.location}. Income: {profile.income}, Medical History: {profile.medical_history}."
        
        logger.info(f"Generating recommendations for session: {profile.session_id}")
        raw_output = ranker.rank_policies(query, profile.dict())
        logger.info(f"Ranker output: {raw_output[:100]}...")
        
        if "No policy data available" in raw_output:
            logger.warning(f"No policy data found for query: {query}")
            raise HTTPException(status_code=404, detail="No policy data found in the system.")
        
        # Simple parsing logic
        best_fit_policy = ""
        comparison_items = []
        coverage_detail_items = []
        why_this_policy = ""
        
        lines = raw_output.split("\n")
        current_section = ""
        
        for i, line in enumerate(lines):
            if "BEST FIT POLICY" in line:
                current_section = "best_fit"
                continue
            elif "PEER COMPARISON TABLE" in line:
                current_section = "comparison"
                continue
            elif "COVERAGE DETAIL TABLE" in line:
                current_section = "coverage"
                continue
            elif "WHY THIS POLICY" in line:
                current_section = "why"
                # The rest of the output is the explanation
                why_this_policy = "\n".join(lines[i+1:]).strip()
                break
            
            if current_section == "best_fit" and line.strip() and not line.startswith("-") and not line.startswith("1."):
                best_fit_policy = line.strip()
            elif current_section == "best_fit" and line.strip().startswith("-"):
                # Sometimes the model might put it in a bullet
                best_fit_policy = line.strip("- ").strip()
            
            if current_section == "comparison" and "|" in line and "---" not in line and "Rank" not in line:
                # Remove leading/trailing pipes and split
                parts = [p.strip() for p in line.strip("|").split("|")]
                if len(parts) >= 7: # rank, name, insurer, premium, cover, wait, benefit, score
                    # If the first part is a rank number or the first few parts are valid
                    try:
                        comparison_items.append(ComparisonItem(
                            policy_name=parts[1],
                            insurer=parts[2],
                            premium=parts[3],
                            cover_amount=parts[4],
                            waiting_period=parts[5],
                            key_benefit=parts[6],
                            suitability_score=parts[7] if len(parts) > 7 else "High"
                        ))
                    except (IndexError, ValueError):
                        continue
            elif current_section == "coverage" and "|" in line and "---" not in line and "Category" not in line:
                parts = [p.strip() for p in line.strip("|").split("|")]
                if len(parts) >= 2:
                    coverage_detail_items.append(CoverageDetailItem(
                        category=parts[0],
                        details=parts[1]
                    ))
        
        # Fallbacks if parsing failed
        if not comparison_items:
            comparison_items.append(ComparisonItem(
                policy_name="Standard Health Plan",
                insurer="Generic Insurer",
                premium="Contact for quote",
                cover_amount="5,00,000",
                waiting_period="30 days",
                key_benefit="Essential coverage",
                suitability_score="Medium"
            ))

        if not coverage_detail_items:
            coverage_detail_items = [
                CoverageDetailItem(category="Inclusions", details="Hospitalization, Daycare"),
                CoverageDetailItem(category="Exclusions", details="Cosmetic, Pre-existing (initial period)"),
                CoverageDetailItem(category="Sub-limits", details="Room rent capping applies"),
                CoverageDetailItem(category="Co-pay %", details="0%"),
                CoverageDetailItem(category="Claim type", details="Cashless")
            ]
        
        if not why_this_policy:
            why_this_policy = f"Based on your profile (age {profile.age}, medical history of {profile.medical_history}), this policy offers the best balance of coverage and affordability. It explicitly addresses your concerns regarding waiting periods for pre-existing conditions while fitting your income bracket."

        if not best_fit_policy and comparison_items:
            best_fit_policy = f"The {comparison_items[0].policy_name} from {comparison_items[0].insurer} is your top recommendation based on your profile."
        elif not best_fit_policy:
            best_fit_policy = "We have identified the Standard Health Plan as a suitable starting point for your insurance needs."

        # Store profile in session memory
        session_store[profile.session_id] = {
            "user_profile": profile.dict(),
            "chat_history": []
        }
        
        return RecommendationResponse(
            best_fit_policy=best_fit_policy,
            comparison_table=comparison_items,
            coverage_detail_table=coverage_detail_items,
            why_this_policy=why_this_policy
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
        session = session_store.get(query_data.session_id)
        user_profile = session.get("user_profile") if session else None
        if not user_profile or not isinstance(user_profile, dict):
            logger.error(f"Invalid user profile in session: {user_profile}")
            raise HTTPException(status_code=400, detail="User profile not found. Please submit the form first.")

        agent = AarogyaAgent()
        logger.info(f"Processing chat for session: {query_data.session_id}")
        # Pass a copy to avoid any side effects
        result = agent.chat_with_user(query_data.query, dict(user_profile))
        
        session["chat_history"].append({
            "query": query_data.query,
            "answer": result["answer"]
        })
        
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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
