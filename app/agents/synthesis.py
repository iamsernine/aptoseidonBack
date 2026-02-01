from app.models import RiskAnalysis, CredibilityAnalysis, FinalReport
from app import llm
import json

async def synthesize_report(
    risk: RiskAnalysis, 
    cred: CredibilityAnalysis, 
    market_data: dict = None, 
    rule_results: list = None,
    narrative_text: str = None,
    conflict_data: dict = None,
    fin_analysis: dict = None
) -> FinalReport:
    """
    Synthesizes all agent outputs into a final consistent report.
    """
    # 1. Calculate weighted safety score
    # Risk 1.0 = Dangerous. Cred 1.0 = Safe.
    final_score = ((1.0 - risk.risk_score) * 0.6) + (cred.credibility_score * 0.4)
    
    # 2. Confidence Decomposition
    conf_details = {
        "on_chain": 0.9 if (market_data or risk.risk_score != 0.5) else 0.5,
        "social": 0.7 if cred.positive_signals else 0.4,
        "consistency": 0.9 if not (conflict_data and conflict_data.get("has_conflict")) else 0.4
    }

    # 3. Final Summary (Human-readable synthesis)
    # Uses the structural narrative as a base
    summary_prompt = f"""
    Risk Score: {risk.risk_score}
    Credibility Score: {cred.credibility_score}
    Structural Narrative: {narrative_text}
    Conflict Detected: {conflict_data.get('has_conflict') if conflict_data else False}
    """
    
    verdict_text = await llm.get_text_completion(
        "Generate a 2-sentence executive summary. Stay factual and neutral.",
        summary_prompt
    )

    return FinalReport(
        final_score=final_score,
        summary=verdict_text or "Analysis complete.",
        verdict="Structural Assessment Finalized.", 
        confidence=0.95, 
        confidence_details=conf_details,
        risk=risk,
        credibility=cred,
        financial_analysis=fin_analysis,
        rule_results=rule_results or [],
        agent_conflict=conflict_data,
        narrative=narrative_text
    )
