import os
import logging
from typing import Dict, Any, List, Optional
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
logger = logging.getLogger("InsuranceAgent")

# Load environment variables
load_dotenv()

class InsuranceAgent:
    """
    Intelligent Agent for insurance policy comparison and recommendation.
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
You are a senior insurance AI agent. Your goal is to compare insurance policies and provide personalized recommendations.

STRICT RULES:
1. You MUST use ALL 6 user profile fields in your reasoning and suitability table:
   - age, gender, income, dependents, medical_history, location
2. You MUST ONLY use information provided in the "Retrieved Policy Context".
3. DO NOT hallucinate, assume, or use external knowledge about insurance policies.
4. If a specific detail (like premium, waiting period, etc.) is missing in the context, explicitly state "Not mentioned in policy".
5. Citations are MANDATORY. Use format: "According to [Source, Page X]..."

OUTPUT STRUCTURE (Follow this exact order):
1. POLICY COMPARISON TABLE:
   | Policy Name | Premium | Coverage | Waiting Period | Key Benefits | Limitations |
   |-------------|---------|----------|----------------|--------------|-------------|

2. COVERAGE SUITABILITY TABLE:
   | Criteria | User Need | Policy Match | Verdict |
   |----------|-----------|--------------|---------|
   (Note: Use all 6 profile fields as criteria)

3. FINAL RECOMMENDATION:
   - Identify the BEST policy or state "No suitable policy found".
   - Provide clear justification based on the user profile and policy facts.

4. EXPLANATION:
   - Detailed breakdown of why the recommendation was made.
   - Transparent reasoning with source citations.
"""

    def _validate_profile(self, user_profile: Dict[str, Any]) -> bool:
        """Checks if all mandatory fields are present in the user profile."""
        return all(field in user_profile and user_profile[field] is not None for field in self.REQUIRED_PROFILE_FIELDS)

    def run(self, query: str, user_profile: Dict[str, Any]) -> str:
        """
        Executes the agent logic: Validation -> Retrieval -> Reasoning -> Output.
        """
        # 1. Validate User Profile
        if not self._validate_profile(user_profile):
            logger.error(f"Incomplete profile provided: {user_profile}")
            return "Incomplete user profile. Cannot proceed."

        # 2. Retrieve Relevant Chunks
        logger.info(f"Retrieving context for query: {query}")
        chunks = retrieve_policy_chunks(query)
        
        if not chunks:
            logger.warning("No relevant policy data found.")
            return "No relevant policy data found."

        # 3. Build Context String
        context = build_context(chunks)

        # 4. Prepare Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "User Profile:\n{user_profile}\n\nRetrieved Policy Context:\n{context}\n\nUser Question: {query}")
        ])

        # 5. Execute Chain
        try:
            logger.info("Generating agent response...")
            chain = prompt | self.llm | StrOutputParser()
            response = chain.invoke({
                "user_profile": user_profile,
                "context": context,
                "query": query
            })
            return response
        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}")
            return f"An error occurred during agent execution: {str(e)}"

if __name__ == "__main__":
    # Set encoding for Windows console
    import sys
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # Example Usage
    agent = InsuranceAgent()
    
    # 1. Sample User Profile
    sample_profile = {
        "age": 35,
        "gender": "Male",
        "income": "75,000 USD/year",
        "dependents": "Spouse and 2 children",
        "medical_history": "No major illnesses, occasional back pain",
        "location": "New York, USA"
    }
    
    # 2. Sample Query
    sample_query = "I need a policy that covers my family and provides good maternity benefits if we decide to have another child."
    
    print("\n--- Insurance Agent Analysis ---\n")
    result = agent.run(sample_query, sample_profile)
    print(result)
