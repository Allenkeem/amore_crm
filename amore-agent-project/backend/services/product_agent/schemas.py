from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field

# --- Input Schema ---
class RetrievalRequest(BaseModel):
    user_query: str
    user_context: Optional[Dict[str, Any]] = {}
    session_history: Optional[List[str]] = []

# --- Output Components ---
class MatchDetails(BaseModel):
    matched_entities: List[str] = []
    matched_attributes: List[str] = []
    filters_applied: List[str] = []

class FactsheetSignals(BaseModel):
    EFFICACY: List[str] = []
    PURCHASE: List[str] = []

class VoiceInfo(BaseModel):
    key_claims: List[str] = []
    usage: List[str] = []
    signals: FactsheetSignals = Field(default_factory=FactsheetSignals)

class OfficialInfo(BaseModel):
    extracted_facts: List[str] = [] # From news_cards
    # Can add more fields later like ingredients, etc.

class Factsheet(BaseModel):
    product_id: str = ""
    category: str = "Unknown"
    official_info: OfficialInfo = Field(default_factory=OfficialInfo)
    voice_info: VoiceInfo = Field(default_factory=VoiceInfo)
    # Deprecated fields - kept for backward compatibility if needed, but better to move
    # key_claims, usage, signals moved to VoiceInfo

class EvidenceHighlight(BaseModel):
    type: str # 'review_snippet' | 'topic_keyword'
    text: str

class Evidence(BaseModel):
    highlights: List[EvidenceHighlight] = []

class ProductCandidate(BaseModel):
    rank: int
    product_id: str
    brand: str
    product_name: str
    score: float
    match: MatchDetails = Field(default_factory=MatchDetails)
    factsheet: Factsheet = Field(default_factory=Factsheet)
    evidence: Evidence = Field(default_factory=Evidence)

# --- Final Output Schema ---
class RetrievalResponse(BaseModel):
    query: str
    retrieval_version: str = "m1.v0.1"
    top_k: int
    candidates: List[ProductCandidate] = []
