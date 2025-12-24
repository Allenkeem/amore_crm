import os

# Base Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Backend Data Root (backend/data)
BACKEND_DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../data"))

PRODUCT_AGENT_DATA = os.path.join(BACKEND_DATA_DIR, "product_agent")
CRM_AGENT_DATA = os.path.join(BACKEND_DATA_DIR, "crm_agent")

# Data Files
PRODUCT_CARDS_PATH = os.path.join(PRODUCT_AGENT_DATA, "product_cards.jsonl")
NEWS_CARDS_PATH = os.path.join(PRODUCT_AGENT_DATA, "news_cards.jsonl")
TOPIC_CARDS_PATH = os.path.join(PRODUCT_AGENT_DATA, "topic_cards.jsonl")
PERSONA_CARDS_PATH = os.path.join(CRM_AGENT_DATA, "persona_cards.jsonl")

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
