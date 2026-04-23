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

STRICT RULES:
1. You MUST use ALL 6 user profile fields in your reasoning:
   - age, gender, income, dependents, medical_history, location
2. You MUST ONLY use information from the provided "Retrieved Policy Context".
3. DO NOT hallucinate or assume policy details. If a detail is missing, say "Not mentioned in policy".
4. DO NOT use external knowledge.
5. DO NOT use rigid scoring formulas. Use contextual reasoning to balance trade-offs (e.g., higher premium but better coverage).
6. Rank from BEST to WORST.

OUTPUT FORMAT (STRICT):

1. POLICY RANKING TABLE:
| Rank | Policy Name | Affordability | Disease Match | Waiting Period | Benefits Score | Overall Reason |
|------|------------|---------------|---------------|----------------|----------------|----------------|
- Use qualitative scores: High / Medium / Low.
- Overall Reason must be 1–2 lines.

2. TOP RECOMMENDATION:
- Clearly identify the BEST policy.
- Justify using the user profile and retrieved data.

3. DETAILED REASONING:
- For each policy, explain the ranking position and trade-offs.
- Use citations: "According to [Source, Page X]...".

4. EDGE CASE HANDLING:
- If no policies match well: "No strongly suitable policy found based on the given criteria."
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
