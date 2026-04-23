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
PERSIST_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = -1.0  # Temporarily disabled threshold to allow all top-K matches
TOP_K = 15

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
    Ensures diversity of sources if possible.
    """
    if not query or not query.strip():
        return []

    vector_store = get_vector_store()
    if not vector_store:
        return []

    try:
        # Increase k to get a pool of candidates for diversity
        results = vector_store.similarity_search_with_relevance_scores(query, k=TOP_K * 2)
        
        formatted_results = []
        seen_chunks = set()
        source_counts = {} # Track how many chunks from each source

        for doc, score in results:
            if score < SIMILARITY_THRESHOLD:
                continue

            chunk_id = doc.metadata.get("chunk_id", doc.page_content)
            source = doc.metadata.get("source", "Unknown")
            
            if chunk_id in seen_chunks:
                continue
            
            # Limit chunks per source to ensure variety in the final context
            if source_counts.get(source, 0) >= 5:
                continue

            seen_chunks.add(chunk_id)
            source_counts[source] = source_counts.get(source, 0) + 1

            formatted_results.append({
                "content": doc.page_content,
                "source": source,
                "page": doc.metadata.get("page", 0),
                "policy_name": doc.metadata.get("policy_name", "Unknown"),
                "insurer": doc.metadata.get("insurer", "Unknown"),
                "score": round(float(score), 4)
            })

            if len(formatted_results) >= TOP_K:
                break

        logger.info(f"Retrieved {len(formatted_results)} chunks from {len(source_counts)} unique sources.")
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
        policy_info = f"Policy: {chunk.get('policy_name', 'Unknown')}, Insurer: {chunk.get('insurer', 'Unknown')}"
        ref = f"[Source: {chunk['source']}, Page: {chunk['page']}, {policy_info}]"
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

def list_indexed_policies() -> List[Dict[str, Any]]:
    """
    Returns a list of unique policies with metadata (source, upload_date, type, policy_name, insurer).
    """
    vector_store = get_vector_store()
    if not vector_store:
        return []

    try:
        data = vector_store.get()
        if not data or 'metadatas' not in data:
            return []
        
        unique_policies = {}
        for meta in data['metadatas']:
            source = meta.get('source')
            if source and source not in unique_policies:
                unique_policies[source] = {
                    "source": source,
                    "policy_name": meta.get("policy_name", "Unknown"),
                    "insurer": meta.get("insurer", "Unknown"),
                    "upload_date": meta.get("upload_date", "Unknown"),
                    "file_type": source.split('.')[-1].upper() if '.' in source else "UNKNOWN"
                }
        
        return list(unique_policies.values())
    except Exception as e:
        logger.error(f"Error listing policies: {str(e)}")
        return []

def update_policy_metadata(source: str, new_metadata: Dict[str, Any]) -> bool:
    """
    Updates metadata for all chunks of a specific policy source.
    """
    vector_store = get_vector_store()
    if not vector_store:
        return False

    try:
        # 1. Get all documents for this source
        data = vector_store.get(where={"source": source})
        if not data or not data['ids']:
            return False

        # 2. Update metadata for each chunk
        for i in range(len(data['ids'])):
            doc_id = data['ids'][i]
            existing_meta = data['metadatas'][i]
            existing_meta.update(new_metadata)
            
            # Re-add with same ID to update
            # Chroma doesn't have a direct 'update' for metadata in the same way, 
            # so we use add_documents with IDs or delete and re-add.
            # Simplified for this requirement:
            vector_store._collection.update(
                ids=[doc_id],
                metadatas=[existing_meta]
            )
            
        logger.info(f"Updated metadata for {source}")
        return True
    except Exception as e:
        logger.error(f"Error updating metadata: {str(e)}")
        return False

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
