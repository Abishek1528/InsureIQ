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

    def _get_chat_system_prompt(self) -> str:
        return """
You are a senior insurance AI assistant named AarogyaAid. Your goal is to provide personalized, contextual, and grounded answers about insurance policies with warmth and empathy.

USER PROFILE (MANDATORY CONTEXT):
Use these details to personalize your response and generate realistic scenarios:
- Age: {age}
- Gender: {gender}
- Income: {income}
- Dependents: {dependents}
- Medical History: {medical_history}
- Location: {location}

STRICT RULES:
1. Grounding: Every factual claim MUST cite the source policy document using format: "According to [Source, Page X]...". Ungrounded claims are a fail.
2. Empathy: Acknowledge the user's situation. Use warmth, not clinical detachment.
3. Term Definition: If the user asks about insurance terms (deductible, co-pay, sub-limit, waiting period, exclusion), define them accurately in plain English.
4. Example Case Generation: When a user asks how a policy applies to them, generate a realistic scenario using their actual health condition and city (from their profile).
5. No Hallucinations: If info is missing in the context, say "Not mentioned in policy".
6. Answer Style: 
   - Clear, conversational, and personalized.
   - 4–8 sentences.
   - Include reasoning.
7. Tone: "Since you mentioned living in {location} with a history of {medical_history}, it's important to note that co-pay (which is the portion you pay during a claim) might work like this for you..."

Your response must be a single string containing your answer.
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
            logger.error(f"Ranking execution failed: {str(e)}")
            return f"An error occurred during ranking: {str(e)}"

    def chat_with_user(self, query: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes personalized conversational chat logic using LangChain and Groq.
        """
        # 1. Retrieve Relevant Chunks
        logger.info(f"Retrieving context for chat query: {query}")
        chunks = retrieve_policy_chunks(query)
        
        if not chunks:
            return {
                "answer": "No relevant policy information found.",
                "sources": []
            }

        # 2. Build Context String
        context = build_context(chunks)

        # 3. Prepare Prompt
        # Format the system prompt with user profile details
        chat_system_prompt = self._get_chat_system_prompt().format(
            age=user_profile.get("age", "N/A"),
            gender=user_profile.get("gender", "N/A"),
            income=user_profile.get("income", "N/A"),
            dependents=user_profile.get("dependents", "N/A"),
            medical_history=user_profile.get("medical_history", "N/A"),
            location=user_profile.get("location", "N/A")
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", chat_system_prompt),
            ("human", "Retrieved Policy Context:\n{context}\n\nUser Question: {query}")
        ])

        # 4. Execute Chain
        try:
            logger.info("Generating personalized chat response...")
            chain = prompt | self.llm | StrOutputParser()
            answer = chain.invoke({
                "context": context,
                "query": query
            })

            # 5. Extract Sources
            sources = []
            seen_sources = set()
            for chunk in chunks:
                source_key = f"{chunk['source']}_{chunk['page']}"
                if source_key not in seen_sources:
                    sources.append({
                        "source": chunk['source'],
                        "page": chunk['page']
                    })
                    seen_sources.add(source_key)

            return {
                "answer": answer,
                "sources": sources
            }
        except Exception as e:
            logger.error(f"Chat execution failed: {str(e)}")
            return {
                "answer": f"An error occurred during chat: {str(e)}",
                "sources": []
            }

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
