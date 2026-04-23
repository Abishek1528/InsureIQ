import pytest
import os
from retrieval import retrieve_policy_chunks, get_vector_store

def test_retrieval_works():
    """
    Production-quality unit test for the RAG retrieval function.
    Verifies data structure, content relevance, and vector DB connectivity.
    """
    
    # 1. Setup & Pre-check: Ensure the vector store is accessible
    vector_store = get_vector_store()
    if vector_store is None:
        pytest.fail("Failed to load vector store. Check PERSIST_DIRECTORY and embedding model initialization.")

    # 2. Data Presence Check: Skip if DB is empty instead of failing
    # We use the underlying Chroma client to check for existing IDs
    db_data = vector_store.get()
    if not db_data or not db_data.get('ids'):
        pytest.skip("No data found in vector DB. Ingest a policy before running this test.")

    # 3. Execution: Run retrieval with a common insurance-related query
    test_query = "waiting period"
    results = retrieve_policy_chunks(test_query)

    # 4. Basic Structure Assertions
    # Verify function returns a list
    assert isinstance(results, list), f"Expected list, got {type(results).__name__}"
    
    # Verify results are not empty (since we checked data presence above)
    assert len(results) > 0, f"No results found for query: '{test_query}'"

    # 5. Field & Type Validation
    required_fields = {"content", "source", "page", "score"}
    
    for i, chunk in enumerate(results):
        # Ensure all required keys exist in the response dictionary
        missing_keys = required_fields - set(chunk.keys())
        assert not missing_keys, f"Result at index {i} is missing fields: {missing_keys}"

        # Validate data types
        assert isinstance(chunk["content"], str), f"Content at index {i} must be a string"
        assert isinstance(chunk["source"], str), f"Source at index {i} must be a string"
        assert isinstance(chunk["page"], int), f"Page at index {i} must be an integer"
        assert isinstance(chunk["score"], float), f"Score at index {i} must be a float"

        # Validate content is not empty
        assert len(chunk["content"].strip()) > 0, f"Empty content found at index {i}"

    # 6. Score Range Validation
    # In ChromaDB with similarity_search_with_relevance_scores, scores are typically 0 to 1
    # where 1 is a perfect match (depending on the distance metric used)
    for i, chunk in enumerate(results):
        score = chunk["score"]
        assert score is not None, f"Score at index {i} is None"
        # Basic check to ensure score is a valid float number
        assert not (score != score), f"Score at index {i} is NaN" 

    # 7. Content Relevance Validation (Basic Keyword Check)
    # Check if at least one result contains words related to the query
    relevance_keywords = ["wait", "period", "day", "month", "year", "exclusion"]
    found_relevant_text = any(
        any(keyword.lower() in chunk["content"].lower() for keyword in relevance_keywords)
        for chunk in results
    )
    
    assert found_relevant_text, f"None of the top {len(results)} results contained relevant keywords for '{test_query}'"

if __name__ == "__main__":
    # Allow running this file directly with 'python test_retrieval.py'
    pytest.main([__file__])
