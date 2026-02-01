from app.models import CollectorData, RiskAnalysis
from app import llm
import json
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a blockchain risk verification agent. 
Analyze the provided website text for a crypto project.
Identify:
1. Technical Risks (e.g. unverified contracts, no audit mentioned). 
   - NOTE: If the project is a Layer 1 blockchain (like Bitcoin, Ethereum) or a Wallet, the absence of smart contracts is NOT a risk.
2. Financial Risks (e.g. high APY promises, ponzi-nomics).
3. Extract "Risk Flags" as bullet points.
4. Assign a Risk Score (0.0 to 1.0, where 1.0 is EXTREME RISK / DANGEROUS, 0.0 is SAFE).

Output valid JSON only:
{
    "risk_score": float, 
    "risk_flags": ["flag1", "flag2"]
}
"""

async def assess_risk(data: CollectorData) -> RiskAnalysis:
    text_content = data.raw_signals.get("text_content", "")
    
    # Construct Context
    context = f"Website Content: {text_content[:2000]}\n"
    if data.market_data:
        context += f"Market Data (CoinGecko): {data.market_data}\n"
    if data.on_chain_data:
        context += f"On-Chain Data: {data.on_chain_data}\n"

    # Allow processing if we have ANY data (Market or Chain), even if no text
    if not text_content and not data.market_data and not data.on_chain_data:
        return RiskAnalysis(risk_score=0.5, risk_flags=["No content found to analyze"])

    try:
        json_str = await llm.get_json_completion(SYSTEM_PROMPT, context)
        if json_str:
            res = json.loads(json_str)
            return RiskAnalysis(
                risk_score=res.get("risk_score", 0.5),
                risk_flags=res.get("risk_flags", [])
            )
    except Exception as e:
        logger.error(f"Risk Analysis failed: {e}")
    
    # Fallback
    return RiskAnalysis(risk_score=0.5, risk_flags=["AI Analysis Error, manual review required"])
