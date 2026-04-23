# Dependencies to install:
# pip install langchain chromadb sentence-transformers langchain-huggingface

import os
import logging
from typing import List, Dict, Any, Optional

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("RAG-Retrieval")

# Configuration
PERSIST_DIRECTORY = "./chroma_db"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = -1.0  # Temporarily disabled threshold to allow all top-K matches
TOP_K = 5

# Global variable to cache the vector store
_vector_store = None

def get_vector_store():
    """
    Initializes and returns the singleton Chroma vector store instance.
    """
    global _vector_store
    if _vector_store is None:
        try:
            logger.info(f"Loading Vector Store from {PERSIST_DIRECTORY}...")
            if not os.path.exists(PERSIST_DIRECTORY):
                logger.error(f"Vector store directory not found: {PERSIST_DIRECTORY}")
                return None

            embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
            _vector_store = Chroma(
                persist_directory=PERSIST_DIRECTORY,
                embedding_function=embeddings
            )
            logger.info("Vector Store loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            return None
    return _vector_store

def retrieve_policy_chunks(query: str) -> List[Dict[str, Any]]:
    """
    Retrieves the most relevant chunks from the vector database for a given query.
    
    Args:
        query (str): The search query.
        
    Returns:
        List[Dict[str, Any]]: A list of structured results with content, source, page, and score.
    """
    # 1. Validation
    if not query or not query.strip():
        logger.warning("Empty query received. Returning empty list.")
        return []

    # 2. Get Vector Store
    vector_store = get_vector_store()
    if not vector_store:
        logger.error("Failed to retrieve vector store. Check your DB path and embeddings.")
        return []

    try:
        # 3. Retrieval with Scores
        # Note: similarity_search_with_relevance_scores is often preferred for thresholding
        results = vector_store.similarity_search_with_relevance_scores(query, k=TOP_K)
        
        formatted_results = []
        seen_chunks = set() # For duplicate removal

        for doc, score in results:
            # 4. Score Threshold Filtering
            if score < SIMILARITY_THRESHOLD:
                continue

            chunk_id = doc.metadata.get("chunk_id", doc.page_content)
            
            # 5. Duplicate Removal
            if chunk_id in seen_chunks:
                continue
            seen_chunks.add(chunk_id)

            # 6. Structuring Output
            formatted_results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page", 0),
                "score": round(float(score), 4)
            })

        logger.info(f"Retrieved {len(formatted_results)} relevant chunks for query: '{query}'")
        return formatted_results

    except Exception as e:
        logger.error(f"Error during retrieval: {str(e)}", exc_info=True)
        return []

def build_context(chunks: List[Dict[str, Any]]) -> str:
    """
    Combines retrieved chunks into a clean context string for LLM input.
    
    Args:
        chunks (List[Dict[str, Any]]): List of retrieved chunk dictionaries.
        
    Returns:
        str: Formatted context string with source references.
    """
    if not chunks:
        return "No relevant context found."

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        ref = f"[Source: {chunk['source']}, Page: {chunk['page']}]"
        context_parts.append(f"--- Chunk {i} {ref} ---\n{chunk['content']}")

    return "\n\n".join(context_parts)

def delete_policy_from_db(file_name: str) -> bool:
    """
    Deletes all chunks associated with a specific file from the vector store.
    """
    vector_store = get_vector_store()
    if not vector_store:
        logger.error("Failed to retrieve vector store for deletion.")
        return False

    try:
        # ChromaDB delete using metadata filter
        logger.info(f"Deleting embeddings for source: {file_name}")
        vector_store.delete(where={"source": file_name})
        logger.info(f"Successfully deleted all chunks for {file_name} from ChromaDB.")
        return True
    except Exception as e:
        logger.error(f"Error deleting {file_name} from ChromaDB: {str(e)}")
        return False

def list_indexed_policies() -> List[str]:
    """
    Returns a list of unique policy file names indexed in the vector store.
    """
    vector_store = get_vector_store()
    if not vector_store:
        return []

    try:
        # Get all documents to extract unique sources
        # In a very large DB, this might be slow; but for policy PDFs, it's efficient enough
        data = vector_store.get()
        if not data or 'metadatas' not in data:
            return []
        
        sources = set()
        for meta in data['metadatas']:
            if 'source' in meta:
                sources.add(meta['source'])
        
        return sorted(list(sources))
    except Exception as e:
        logger.error(f"Error listing policies from ChromaDB: {str(e)}")
        return []

if __name__ == "__main__":
    # Set encoding for Windows console
    import sys
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # Example usage:
    test_query = "What is the coverage limit for medical expenses?"
    retrieved_data = retrieve_policy_chunks(test_query)
    
    if retrieved_data:
        context_for_llm = build_context(retrieved_data)
        print("\n=== RETRIEVED CONTEXT ===\n")
        print(context_for_llm)
    else:
        print("No relevant results found.")
