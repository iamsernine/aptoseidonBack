# Aptoseidon Agentic Backend

FastAPI backend for Aptoseidon, an agent-driven crypto analysis platform.

## Features
- Multi-agent orchestration for crypto project analysis.
- x402 payment verification on Aptos.
- SQLite persistence for results and reputation.

## Deployment
This project is configured for deployment on Render/Railway.
Build Command: `poetry install`
Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
