from app.models import CollectorData, RuleResult

# RuleResult is now imported from models.py to avoid Pydantic type mismatch

def check_liquidity(data: CollectorData) -> RuleResult:
    if not data.market_data:
        return RuleResult(rule_id="LIQ_UNKNOWN", status="WARN", reason="No market data available", source="CoinGecko")
    
    mcap = data.market_data.get("market_cap", 0)
    vol = data.market_data.get("vol_24h", 0)
    
    if mcap > 0 and (vol / mcap) < 0.01:
        return RuleResult(rule_id="LIQ_GHOST", status="FAIL", reason="Volume/Mcap ratio < 1% (Ghost Chain)", source="CoinGecko")
    
    return RuleResult(rule_id="LIQ_OK", status="PASS", reason="Liquidity sufficient", source="CoinGecko")

def check_docs(data: CollectorData) -> RuleResult:
    if not data.docs_present:
        return RuleResult(rule_id="DOCS_MISSING", status="FAIL", reason="No documentation or whitepaper detected", source="WebScraper")
    return RuleResult(rule_id="DOCS_OK", status="PASS", reason="Documentation found", source="WebScraper")

def check_contracts(data: CollectorData) -> RuleResult:
    # Logic: If it's a token/contract/defi, it SHOULD have contracts.
    # But we don't strictly know the intent yet.
    if data.contracts_found:
        return RuleResult(rule_id="CONTRACT_FOUND", status="PASS", reason="Smart Contract detected", source="AptosNode")
    
    # If it looks like an address but no modules
    return RuleResult(rule_id="CONTRACT_MISSING", status="WARN", reason="No modules found at address", source="AptosNode")

def run_all_rules(data: CollectorData) -> List[RuleResult]:
    results = []
    results.append(check_docs(data))
    results.append(check_liquidity(data))
    # Add more as needed
    return results
