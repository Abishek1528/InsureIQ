# Dependencies to install:
# pip install langchain langchain-openai langchain-community pypdf chromadb python-dotenv tiktoken langchain-huggingface sentence-transformers langchain-groq

import os
import shutil
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader, JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import json

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

def ingest_policy(file_path: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Processes an insurance policy (PDF, JSON, TXT) and stores it in a vector database.
    """
    try:
        # 1. Validation
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return

        file_name = os.path.basename(file_path)
        file_ext = file_name.split('.')[-1].lower()
        
        # 2. Embedding Initialization
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

        # 3. Vector Store
        vector_store = Chroma(
            persist_directory=PERSIST_DIRECTORY,
            embedding_function=embeddings
        )

        # 4. Loading
        logger.info(f"Loading {file_ext} file: {file_path}")
        if file_ext == 'pdf':
            loader = PyPDFLoader(file_path)
            pages = loader.load()
        elif file_ext == 'json':
            # Simple JSON loader - loads entire content as one doc
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            pages = [Document(page_content=json.dumps(content), metadata={"source": file_name})]
        else: # txt
            loader = TextLoader(file_path, encoding='utf-8')
            pages = loader.load()
        
        # 5. Text Chunking
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            model_name="gpt-4",
            chunk_size=700,
            chunk_overlap=100,
            add_start_index=True,
        )
        
        chunks = text_splitter.split_documents(pages)
        
        # 6. Metadata Enrichment
        for i, chunk in enumerate(chunks):
            chunk.metadata["source"] = file_name
            chunk.metadata["chunk_id"] = f"{file_name}_{i}"
            if metadata:
                chunk.metadata.update(metadata)

        # 7. Store in Chroma
        vector_store.add_documents(chunks)
        logger.info(f"Successfully ingested '{file_name}' into ChromaDB.")
        
    except Exception as e:
        logger.error(f"An error occurred during ingestion: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # This will now run when you type 'python main.py'
    ingest_policy("policy.pdf") 
