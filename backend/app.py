import os
import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from retrieval import retrieve_policy_chunks, build_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RAG-App")

# Load environment variables (GROQ_API_KEY)
load_dotenv()

def query_policy(question: str):
    """
    Main application flow: Question -> Retrieval -> LLM -> Answer
    """
    try:
        # 1. Retrieve relevant chunks
        logger.info(f"Retrieving context for: {question}")
        chunks = retrieve_policy_chunks(question)
        
        if not chunks:
            return "I'm sorry, I couldn't find any relevant information in the policy to answer that question."

        # 2. Build context string
        context = build_context(chunks)

        # 3. Initialize Groq LLM
        llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )

        # 4. Create Prompt Template
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert insurance assistant. Use the provided context to answer the user's question accurately. If the answer is not in the context, say you don't know based on the policy."),
            ("human", "Context:\n{context}\n\nQuestion: {question}")
        ])

        # 5. Get Answer from LLM
        logger.info("Generating answer using Groq...")
        chain = prompt | llm
        response = chain.invoke({"context": context, "question": question})

        return response.content

    except Exception as e:
        logger.error(f"Error in application flow: {str(e)}")
        return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    # Set encoding for Windows console
    import sys
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # Example interactive loop
    print("--- Insurance Policy AI Assistant ---")
    print("Type 'exit' to quit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        answer = query_policy(user_input)
        print(f"\nAI: {answer}\n")
        print("-" * 30)
