from app.models import CollectorData, RuleResult, RiskAnalysis, CredibilityAnalysis
from app import llm
from typing import List, Optional
import json

SYSTEM_PROMPT = """
You are a Contradiction Agent. 
Compare the Deterministic Rule Results against the AI Agent Analysis.
Identify if there are any major inconsistencies (e.g. Rules say FAIL on liquidity, but AI says LOW RISK).

Output valid JSON:
{
    "has_conflict": bool,
    "reason": "Description of the conflict if any, else empty."
}
"""

async def detect_conflict(rules: List[RuleResult], risk: RiskAnalysis, cred: CredibilityAnalysis) -> dict:
    rules_text = "\n".join([f"- {r.rule_id}: {r.status} - {r.reason}" for r in rules])
    analysis_text = f"""
    AI Risk Score: {risk.risk_score}
    AI Credibility Score: {cred.credibility_score}
    """
    
    context = f"Rules:\n{rules_text}\n\nAI Analysis:\n{analysis_text}"
    
    try:
        json_str = await llm.get_json_completion(SYSTEM_PROMPT, context)
        if json_str:
            return json.loads(json_str)
    except:
        pass
    
    return {"has_conflict": False, "reason": ""}
