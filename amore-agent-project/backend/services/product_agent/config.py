import os

# Base Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../data/rag_documents")

# Data Files
PRODUCT_CARDS_PATH = os.path.join(DATA_DIR, "product_cards.jsonl")
TOPIC_CARDS_PATH = os.path.join(DATA_DIR, "topic_cards.jsonl")
PERSONA_CARDS_PATH = os.path.join(DATA_DIR, "persona_cards.jsonl")

# Retrieval Weights (Re-ranking)
WEIGHTS = {
    "entity_match": 0.35,
    "lexical_score": 0.25,
    "vector_score": 0.25, # Optional, defaults to 0 if not used
    "attribute_match": 0.10,
    "log_review_count": 0.05
}

# Thresholds
RETRIEVAL_TOP_K = 5
CANDIDATE_POOL_SIZE = 100
