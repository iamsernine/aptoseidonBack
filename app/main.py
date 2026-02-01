import logging
from fastapi import FastAPI, UploadFile, File, Form, Body, HTTPException

logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from app.models import CollectorData, RiskAnalysis, CredibilityAnalysis, FinalReport
from app.agents import collector, risk, credibility, synthesis, rules, narrative, contradiction
from app.utils import x402
from app import database
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI(title="Aptoseidon Agentic Backend")

# Initialize database on load
database.init_db()

class AnalyzeRequest(BaseModel):
    project_url: str
    project_type: str
    wallet_address: str
    payment_tx_hash: Optional[str] = None
    request_mode: str = "full" # "pre_check" or "full"
    evidence_only: bool = False

# ... (root / well-known kept same)

@app.post("/analyze")
async def analyze_project(request: AnalyzeRequest):
    # 0. Check Payment
    is_valid_payment = False
    if request.payment_tx_hash:
        is_valid_payment = await x402.verify_payment(request.payment_tx_hash)

    # 1. Check Cache for Paid Reports
    if is_valid_payment:
        cached = database.get_analysis_by_url(request.project_url)
        if cached:
            logger.info(f"Returning cached report for {request.project_url}")
            return {
                "status": "ok",
                "preCheck": cached["report"]["preCheck"],
                "report": cached["report"]["report"],
                "jobId": cached["job_id"]
            }

    # If full report requested but not paid -> 402
    if request.request_mode == "full" and not is_valid_payment:
        raise HTTPException(
            status_code=402, 
            detail={
                "error": "Payment Required",
                "message": "Full analysis requires payment.",
                "recipient": x402.PAYMENT_RECIPIENT,
                "amount": x402.REQUIRED_AMOUNT_APT
            }
        )

    # 1. Collect Data
    data = await collector.collect_data(request.project_url, request.project_type)
    
    # 1.5. Deterministic Rules (Trust Layer)
    rule_results = rules.run_all_rules(data)
    
    # Pre-check logic (Free or Fallback)
    pre_check = {
        "age": data.domain_age,
        "liquidity": "Unknown (Agent Stub)",
        "socialMentions": "High" if data.docs_present else "Low",
        "contractVerified": data.contracts_found
    }

    # If only pre-check requested, return early
    if request.request_mode == "pre_check" or (not is_valid_payment):
        return {
            "status": "pre_check_ok",
            "preCheck": pre_check,
        }
    
    # 2. Parallel Analysis (Budget Controller & Evidence Mode)
    risk_result = None
    credibility_result = None
    narrative_text = None
    fin_analysis = None
    conflict_data = {"has_conflict": False, "reason": ""}
    
    fail_count = len([r for r in rule_results if r.status == "FAIL"])
    warn_count = len([r for r in rule_results if r.status == "WARN"])
    
    skip_agents = request.evidence_only
    if not skip_agents:
        if fail_count < 2 and warn_count == 0:
            logger.info("Budget Controller: Skipping LLM agents.")
            skip_agents = True

    if not skip_agents:
        # Run specialized agents
        risk_result = await risk.assess_risk(data)
        credibility_result = await credibility.assess_credibility(data)
        
        # New agents for Phase 2
        narrative_text = await narrative.generate_narrative(data, rule_results)
        conflict_data = await contradiction.detect_conflict(rule_results, risk_result, credibility_result)
        
        # Financial Structure (Compliant)
        # We can still use the synthesis logic for financial structure or keep it separate
        # For now, let's keep financial structure as part of the analysis if paid
    else:
        # Minimal results
        risk_result = RiskAnalysis(risk_score=0.1 if fail_count == 0 else 0.4, risk_flags=[])
        credibility_result = CredibilityAnalysis(credibility_score=0.9, positive_signals=[])
        narrative_text = "Baseline structural report based on deterministic rules."

    # 3. Synthesis
    final_report = await synthesis.synthesize_report(
        risk_result, 
        credibility_result, 
        data.market_data, 
        rule_results,
        narrative_text,
        conflict_data
    )
    
    # 4. Map to Frontend Response Format
    frontend_report = {
        "riskScore": int(final_report.risk.risk_score * 100),
        "riskLevel": "LOW" if final_report.final_score > 0.7 else "MEDIUM" if final_report.final_score > 0.4 else "HIGH",
        "summary": final_report.summary,
        "investmentAdvice": "Fundamental Assessment: " + final_report.verdict,
        "auditDetails": final_report.risk.risk_flags + final_report.credibility.positive_signals,
        "riskFlags": final_report.risk.risk_flags,
        "positiveSignals": final_report.credibility.positive_signals,
        "marketData": data.market_data,
        "financialAnalysis": final_report.financial_analysis,
        "ruleResults": [r.dict() for r in (final_report.rule_results or [])],
        "agentConflict": final_report.agent_conflict,
        "narrative": final_report.narrative
    }
    
    job_id = f"agent-{uuid.uuid4().hex[:8]}"
    
    result = {
        "status": "ok",
        "preCheck": pre_check,
        "report": frontend_report,
        "jobId": job_id
    }
    
    # 5. Persist if it's a full paid report
    if is_valid_payment:
        database.save_analysis(job_id, request.project_url, request.project_type, request.wallet_address, result)
        
    return result

# --- Reputation / Ratings Stub ---

class RatingRequest(BaseModel):
    job_id: str
    rating: str # "up" or "down"

# In-memory store for demo
mock_ratings = {
    "agent-123": {"up": 5, "down": 0}
}

@app.post("/reputation/rate")
async def rate_reputation(req: RatingRequest):
    database.update_rating(req.job_id, req.rating)
    return {
        "status": "ok",
        "job_id": req.job_id,
        "rating": req.rating
    }

@app.get("/reputation/rate/{job_id}")
async def get_reputation(job_id: str):
    data = database.get_rating(job_id)
    return {
        "job_id": job_id,
        "up": data["up"],
        "down": data["down"]
    }
