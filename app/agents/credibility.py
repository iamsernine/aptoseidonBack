from app.models import CollectorData, CredibilityAnalysis
from app import llm
import json
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a crypto research analyst. 
Analyze the provided website text for a crypto project.
Identify:
1. Team Credibility (anon vs public).
2. Social Proof (partnerships, documentation quality).
3. Extract "Positive Signals".
4. Assign a Credibility Score (0.0 to 1.0, where 1.0 is HIGHLY CREDIBLE).

Output valid JSON only:
{
    "credibility_score": float, 
    "positive_signals": ["signal1", "signal2"]
}
"""

async def assess_credibility(data: CollectorData) -> CredibilityAnalysis:
    text_content = data.raw_signals.get("text_content", "")
    
    # Construct Context
    context = f"Website Content: {text_content[:2000]}\n"
    if data.market_data:
        context += f"Market Data (High Cap is credible): {data.market_data}\n"
    if data.social_signals:
        context += f"Social Search Results (Read for sentiment): {data.social_signals}\n"

    if not text_content and not data.market_data and not data.social_signals:
        return CredibilityAnalysis(credibility_score=0.5, positive_signals=[])

    try:
        json_str = await llm.get_json_completion(SYSTEM_PROMPT, context)
        if json_str:
            res = json.loads(json_str)
            return CredibilityAnalysis(
                credibility_score=res.get("credibility_score", 0.5),
                positive_signals=res.get("positive_signals", [])
            )
    except Exception as e:
        logger.error(f"Credibility Analysis failed: {e}")

    # Fallback
    return CredibilityAnalysis(credibility_score=0.5, positive_signals=[])
