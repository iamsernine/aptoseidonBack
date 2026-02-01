from app.models import CollectorData, RuleResult
from app import llm
from typing import List
import json

SYSTEM_PROMPT = """
You are a Narrative Structural Agent. 
Your job is to convert raw data and hard rule results into a neutral, factual summary of a crypto project's market structure.
- DO NOT use investment advice (Buy/Sell).
- DO NOT use emotional language.
- Focus on: Liquidity depth, Tokenomics (FDV vs Mcap), and Documentation presence.
- Output a 3-sentence structural narrative.
"""

async def generate_narrative(data: CollectorData, rules: List[RuleResult]) -> str:
    rules_summary = "\n".join([f"- {r.rule_id}: {r.status} ({r.reason})" for r in rules])
    
    context = f"""
    Project Name: {data.project_name}
    Market Data: {data.market_data}
    Rule Results:
    {rules_summary}
    """
    
    narrative = await llm.get_text_completion(SYSTEM_PROMPT, context)
    return narrative or "No narrative generated."
