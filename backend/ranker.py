import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from retrieval import retrieve_policy_chunks, build_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("PolicyRanker")

# Load environment variables
load_dotenv()

class PolicyRanker:
    """
    Intelligent Ranker and Recommender for insurance policies using human-like reasoning.
    """
    
    REQUIRED_PROFILE_FIELDS = ["age", "gender", "income", "dependents", "medical_history", "location"]

    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        self.llm = ChatGroq(
            model_name=model_name,
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        return """
You are a senior insurance ranking expert. Your task is to rank and recommend insurance policies based on a user profile and retrieved policy data.

TONE & EMPATHY (CRITICAL):
1. Acknowledge the user's health situation with warmth and empathy BEFORE presenting any numbers or policy names.
2. Define any insurance term (e.g., deductible, co-pay, sub-limit, waiting period, exclusion) the FIRST time it appears in your response. Never leave jargon unexplained.
3. If a policy has high costs or limited coverage, you MUST suggest an alternative path or a "next step" rather than leaving it as a dead end.

STRICT RULES:
1. You MUST use ALL 6 user profile fields in your reasoning:
   - age, gender, income, dependents, medical_history, location
2. You MUST identify and compare ALL distinct policies found in the "Retrieved Policy Context". You must show the recommended policy vs AT LEAST 2 alternatives (minimum 3 policies total in the table).
3. DO NOT hallucinate or assume policy details. If a detail is missing, say "Not mentioned in policy".
4. DO NOT use external knowledge. Only use information from the provided "Retrieved Policy Context".
5. Personalised explanation (WHY THIS POLICY) MUST be between 150-250 words and connect policy features explicitly to at least 3 of the 6 user profile fields. Use a professional, persuasive, yet empathetic tone.

OUTPUT FORMAT (STRICT):

1. PEER COMPARISON TABLE:
| Rank | Policy Name | Insurer | Premium (Rs/yr) | Cover Amount | Waiting Period | Key Benefit | Suitability Score |
|------|------------|---------|-----------------|--------------|----------------|-------------|-------------------|
- Populated from uploaded documents.
- Rank 1 is your TOP recommendation.
- Rank 2 and 3 are the alternatives.
- You MUST show at least 3 rows if the context contains information for multiple policies.

2. COVERAGE DETAIL TABLE:
| Category | Details |
|----------|---------|
- Single-policy breakdown for the TOP RECOMMENDED policy only.
- Categories MUST include: Inclusions, Exclusions, Sub-limits, Co-pay %, Claim type (cashless / reimbursement).
- Data MUST be sourced from the policy document via RAG.

3. WHY THIS POLICY:
- Detailed personalised explanation (STRICTLY 150-250 words).
- Reference at least 3 profile fields (e.g., age, medical_history, income).
- Connect policy features to these fields.
- Explain why this policy is superior to the alternatives mentioned in the table.

4. EDGE CASE HANDLING:
- If retrieved_chunks is empty: "No policy data available for ranking."
"""

    def _validate_profile(self, user_profile: Dict[str, Any]) -> bool:
        """Checks if all mandatory fields are present in the user profile."""
        return all(field in user_profile and user_profile[field] is not None for field in self.REQUIRED_PROFILE_FIELDS)

    def rank_policies(self, query: str, user_profile: Dict[str, Any]) -> str:
        """
        Executes the ranking logic: Validation -> Retrieval -> Reasoning -> Structured Output.
        """
        # 1. Validate User Profile
        if not self._validate_profile(user_profile):
            logger.error(f"Incomplete profile provided: {user_profile}")
            return "Incomplete user profile. Cannot proceed."

        # 2. Retrieve Relevant Chunks
        logger.info(f"Retrieving context for ranking: {query}")
        chunks = retrieve_policy_chunks(query)
        
        if not chunks:
            logger.warning("No relevant policy data found for ranking.")
            return "No policy data available for ranking."

        # 3. Build Context String
        context = build_context(chunks)

        # 4. Prepare Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "User Profile:\n{user_profile}\n\nRetrieved Policy Context:\n{context}\n\nRanking Request: {query}")
        ])

        # 5. Execute Chain
        try:
            logger.info("Generating policy rankings...")
            chain = prompt | self.llm | StrOutputParser()
            response = chain.invoke({
                "user_profile": user_profile,
                "context": context,
                "query": query
            })
            return response
        except Exception as e:
            logger.error(f"Ranking execution failed: {str(e)}")
            return f"An error occurred during ranking: {str(e)}"

if __name__ == "__main__":
    # Set encoding for Windows console
    import sys
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # Example Usage
    ranker = PolicyRanker()
    
    # 1. Sample User Profile
    sample_profile = {
        "age": 45,
        "gender": "Female",
        "income": "120,000 USD/year",
        "dependents": "Elderly parents",
        "medical_history": "Type 2 Diabetes, Hypertension",
        "location": "Mumbai, India"
    }
    
    # 2. Ranking Query
    sample_query = "Rank the best policies for a family with elderly parents and pre-existing conditions like diabetes."
    
    print("\n--- Policy Ranking & Recommendation System ---\n")
    result = ranker.rank_policies(sample_query, sample_profile)
    print(result)
