# InsureIQ: AI-Powered Insurance Advisor (RAG-Based)

## Problem Statement
Insurance selection is complex for the average Indian user due to:
- Lack of clarity on terms like **waiting period**, **co-pay**, and **exclusions**.
- Difficulty comparing multiple similar-looking policies.
- Fear of hidden clauses in policy documents.
- Overwhelming number of options without clear guidance.

This leads to poor decision-making and low confidence in policy selection.

## Target Users
- Middle-class Indian individuals (age 30–50).
- Users with family responsibilities.
- Limited understanding of insurance terminology.
- Looking for affordable and reliable health coverage.

## Solution Overview
InsureIQ is an AI-powered insurance advisor that:
1. **Collects a structured user profile** (6 key inputs).
2. **Uses Retrieval-Augmented Generation (RAG)** on real policy documents.
3. **Compares multiple policies** based on user-specific needs.
4. **Explains results** in simple, personalized, and empathetic language.
5. **Provides a conversational interface (AarogyaAid)** for follow-up queries.

## Core Features

### 1. Profile-Based Recommendation
User inputs (6 key fields as per brief):
- **Full Name**: Personalizes all agent responses and greetings.
- **Age**: Determines premium bracket and waiting period sensitivity.
- **Lifestyle**: (Sedentary/Moderate/Active/Athlete) Adjusts risk weighting.
- **Pre-existing Conditions**: Primary driver for exclusion matching and waiting periods.
- **Annual Income**: Sets coverage amount targets and affordability thresholds.
- **City / Tier**: Adjusts network hospital availability and claim estimates.
These inputs drive all downstream AI reasoning and personalization.

### 2. Policy Comparison (Best Fit Output)
Every recommendation produces three required sections:
- **Peer Comparison Table**: Recommended policy vs. 2-3 alternatives. Includes: Premium, Cover Amount, Waiting Period, etc.
- **Coverage Detail Table**: Single-policy breakdown including Inclusions, Exclusions, Sub-limits, Co-pay %, and Claim type.
- **Why This Policy**: A 150–250 word personalized explanation connecting policy features to at least 3 user profile fields.

### 3. Empathy and Tone
- **Warmth & Empathy**: The agent acknowledges the user's health situation with warmth.
- **Jargon Explainer**: Automatically defines insurance terms (deductible, co-pay, etc.) the first time they appear.
- **Alternative Paths**: High-cost scenarios always end with an alternative suggestion.

### 4. Conversational Chat (AarogyaAid)
- **Session Memory**: Remembers user profile and recommended policy.
- **Source Grounding**: Every factual claim cites the source document: `According to [Source, Page X]...`.

### 5. Admin Panel
- **Multi-Format Upload**: Supports PDF, JSON, and Plain Text formats.
- **Metadata Management**: View and edit Policy Name and Insurer.
- **Secure Access**: Protected by JWT and Bcrypt hashing.

## AI Framework Choice & Justification

| Tool | Choice | Justification |
|------|--------|---------------|
| **LLM** | **Groq (Llama-3.3-70b)** | Chosen for its extreme inference speed and high reasoning capability, essential for real-time complex policy comparisons. |
| **Orchestration** | **LangChain** | Provides a robust framework for RAG pipelines, chat memory management, and prompt templating. |
| **Embeddings** | **HuggingFace (MiniLM-L6)** | Local execution ensures data privacy and zero cost, while providing sufficient semantic accuracy for document retrieval. |
| **Vector DB** | **ChromaDB** | Lightweight, persistent, and easy to integrate with LangChain for semantic search. |

## Recommendation Engine Logic
The `PolicyRanker` follows a strict 4-step execution flow:
1. **Validation**: Ensures all 6 mandatory profile fields are present to ensure personalized reasoning.
2. **Context Retrieval**: Performs a semantic search across indexed policies using the user's query and profile.
3. **Multi-Policy Reasoning**: The LLM analyzes retrieved chunks to identify distinct policies and evaluate them against user constraints (e.g., medical history vs. waiting periods).
4. **Structured Generation**: Produces the 3-section output (Peer Table, Detail Table, Narrative) using strict markdown formatting.

## Document Parsing & RAG Pipeline
The ingestion system handles documents with high precision:
- **Multi-Format Parsing**: Uses `PyPDFLoader` for PDFs, `TextLoader` for TXT, and custom logic for JSON.
- **Recursive Chunking**: Documents are split into **700 token chunks** with a **100 token overlap**. This ensures that important clauses (like exclusions) are not cut in half, maintaining semantic continuity.
- **Metadata Injection**: Every chunk is tagged with `source`, `page`, `policy_name`, and `insurer`. This allows the LLM to provide precise citations and ensures updated metadata from the Admin Panel is reflected in the AI's response.

## Tech Stack

### Backend
- **FastAPI**: Modern, high-performance web framework for the API.
- **LangChain**: Framework for building the RAG pipeline and LLM orchestration.
- **Groq Cloud API**: High-speed inference engine using Llama-3 models.
- **ChromaDB**: Vector database for storing and retrieving policy embeddings.
- **HuggingFace**: Provides local `all-MiniLM-L6-v2` embeddings for semantic search.
- **PyPDF / JSON / Text**: Multi-format document parsing and ingestion.

### Frontend
- **React.js**: Library for building the interactive user and admin interfaces.
- **Fetch API**: For handling communication with the FastAPI backend.

## Setup Instructions

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
# Create .env file with:
# GROQ_API_KEY=your_key
# ADMIN_USERNAME=admin
# ADMIN_PASSWORD=your_password
# SECRET_KEY=your_jwt_secret
python main.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm start
```

## Security
- **JWT Authentication**: Secure session-based admin access.
- **Bcrypt Hashing**: One-way encryption for admin passwords.
- **CORS Middleware**: Restricted origin access (configurable in `main.py`).
