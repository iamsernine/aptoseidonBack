from pydantic import BaseModel
from typing import List, Optional, Any

class CollectorData(BaseModel):
    project_name: str
    domain_age: str
    contracts_found: bool
    docs_present: bool
    raw_signals: dict
    market_data: Optional[dict] = None # Now includes: symbol, ath, atl, fdv, total_supply, circ_supply
    on_chain_data: Optional[dict] = None
    social_signals: Optional[List[str]] = None

class RiskAnalysis(BaseModel):
    risk_score: float
    risk_flags: List[str]

class CredibilityAnalysis(BaseModel):
    credibility_score: float
    positive_signals: List[str]

class RuleResult(BaseModel):
    rule_id: str
    status: str
    reason: str
    source: str

class FinalReport(BaseModel):
    final_score: float
    verdict: str
    confidence: float
    confidence_details: Optional[dict] = None # {on_chain: 0.8, etc}
    summary: str
    risk: RiskAnalysis
    credibility: CredibilityAnalysis
    financial_analysis: Optional[dict] = None
    rule_results: Optional[List[RuleResult]] = None
    agent_conflict: Optional[dict] = None # Item #10
    narrative: Optional[str] = None # Item #6
