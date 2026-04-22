import os
import logging
import sys
import io
from dotenv import load_dotenv
from agent import InsuranceAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RAG-App")

# Load environment variables
load_dotenv()

def main():
    # Set encoding for Windows console to handle special characters
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 1. Initialize the Agent
    agent = InsuranceAgent()

    # 2. Define User Profile (In a real app, this comes from a database or form)
    user_profile = {
        "age": 30,
        "gender": "Female",
        "income": "50k",
        "dependents": "None",
        "medical_history": "Healthy",
        "location": "California"
    }

    print("--- 🛡️ Insurance Policy AI Agent ---")
    print(f"User Profile Loaded: {user_profile['age']}yo {user_profile['gender']} from {user_profile['location']}")
    print("Type 'exit' to quit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        # 3. Run the Agent with the profile
        answer = agent.run(user_input, user_profile)
        print(f"\nAI Agent Response:\n{answer}\n")
        print("-" * 50)

if __name__ == "__main__":
    main()
