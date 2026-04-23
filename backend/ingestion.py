# Dependencies to install:
# pip install langchain langchain-openai langchain-community pypdf chromadb python-dotenv tiktoken langchain-huggingface sentence-transformers langchain-groq

import os
import shutil
import logging
from typing import List, Optional
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_groq import ChatGroq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("RAG-Ingestion")

# Load environment variables
load_dotenv()

# Configuration
PERSIST_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
# Using a free local embedding model instead of OpenAI to avoid quota issues
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def ingest_policy(file_path: str) -> None:
    """
    Processes an insurance policy PDF and stores it in a vector database for retrieval.
    
    Args:
        file_path (str): The absolute or relative path to the PDF file.
        
    Returns:
        None
    """
    try:
        # 0. API Key Check (Groq for later use, Embeddings are free/local now)
        if not os.getenv("GROQ_API_KEY"):
            logger.warning("GROQ_API_KEY not found in environment variables. You'll need it for the LLM part later.")

        # 1. Validation
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return

        file_name = os.path.basename(file_path)
        
        # 2. Embedding Initialization (Free Local Model)
        logger.info(f"Initializing embedding model: {EMBEDDING_MODEL}")
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

        # 3. Handle Vector Store
        # If a DB already exists but with different dimensions (e.g. from OpenAI), we must clear it
        if os.path.exists(PERSIST_DIRECTORY):
            try:
                vector_store = Chroma(
                    persist_directory=PERSIST_DIRECTORY,
                    embedding_function=embeddings
                )
                # Check for duplicate ingestion
                existing_docs = vector_store.get(where={"source": file_name})
                if existing_docs and existing_docs["ids"]:
                    logger.info(f"File '{file_name}' already exists in the vector database. Skipping ingestion.")
                    return
            except Exception as e:
                logger.warning(f"Existing vector store is incompatible or corrupted. Resetting: {e}")
                shutil.rmtree(PERSIST_DIRECTORY)
                vector_store = Chroma(
                    persist_directory=PERSIST_DIRECTORY,
                    embedding_function=embeddings
                )
        else:
            vector_store = Chroma(
                persist_directory=PERSIST_DIRECTORY,
                embedding_function=embeddings
            )

        # 4. PDF Loading
        logger.info(f"Loading PDF: {file_path}")
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        
        # Basic text cleaning
        for page in pages:
            page.page_content = page.page_content.replace("\n", " ").strip()
            
        logger.info(f"Successfully loaded {len(pages)} pages.")

        # 5. Text Chunking
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            model_name="gpt-4",
            chunk_size=700,
            chunk_overlap=100,
            add_start_index=True,
        )
        
        chunks = text_splitter.split_documents(pages)
        logger.info(f"Created {len(chunks)} chunks from {len(pages)} pages.")

        # 6. Metadata Enrichment
        for i, chunk in enumerate(chunks):
            chunk.metadata["source"] = file_name
            chunk.metadata["page"] = chunk.metadata.get("page", 0) + 1
            chunk.metadata["chunk_id"] = f"{file_name}_{i}"

        # 7. Store in Chroma
        logger.info(f"Generating embeddings and storing in ChromaDB...")
        vector_store.add_documents(chunks)
        
        logger.info(f"Successfully ingested and stored '{file_name}' in ChromaDB.")
        
    except Exception as e:
        logger.error(f"An error occurred during ingestion: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # This will now run when you type 'python main.py'
    ingest_policy("policy.pdf") 
