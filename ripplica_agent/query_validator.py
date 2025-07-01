def is_valid_query(query: str) -> bool:
    """
    Returns True if the query is a valid web search query, False otherwise.
    Simple rule: reject queries with commands or tasks (e.g., 'walk my pet').
    """
    # Simple heuristic: reject if query contains verbs like 'add', 'walk', 'remind', 'call', 'email', etc.
    invalid_keywords = ['add', 'walk', 'remind', 'call', 'email', 'set alarm', 'buy', 'order', 'schedule']
    q = query.lower()
    if any(word in q for word in invalid_keywords):
        return False
    # Placeholder for LLM-based validation
    return True 