import os
import logging
import sys
import io
from dotenv import load_dotenv
from ranker import PolicyRanker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Insurance-App")

# Load environment variables
load_dotenv()

def main():
    # Set encoding for Windows console to handle special characters
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 1. Initialize the Ranker (Advanced System)
    ranker = PolicyRanker()

    # 2. Define User Profile
    # In a production app, this would be fetched from a database or a user form
    user_profile = {
        "age": 45,
        "gender": "Female",
        "income": "120,000 USD/year",
        "dependents": "Elderly parents",
        "medical_history": "Type 2 Diabetes, Hypertension",
        "location": "Mumbai, India"
    }

    print("--- 🛡️ Insurance Policy Ranking & Recommendation System ---")
    print(f"User Profile Loaded: {user_profile['age']}yo {user_profile['gender']} from {user_profile['location']}")
    print("Type 'exit' to quit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        if not user_input.strip():
            continue

        # 3. Run the Ranker with the profile
        logger.info(f"Processing request: {user_input}")
        results = ranker.rank_policies(user_input, user_profile)
        
        print(f"\nAI Analysis & Ranking:\n{results}\n")
        print("-" * 50)

if __name__ == "__main__":
    main()
