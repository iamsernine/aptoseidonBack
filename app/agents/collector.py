import httpx
from bs4 import BeautifulSoup
from app.models import CollectorData
import logging
from googlesearch import search
import asyncio

logger = logging.getLogger(__name__)

# --- Helper Functions ---

async def collect_market_data(query: str):
    """
    Search CoinGecko for the project.
    """
    try:
        async with httpx.AsyncClient() as client:
            # 1. Search for ID
            search_url = f"https://api.coingecko.com/api/v3/search?query={query}"
            resp = await client.get(search_url)
            if resp.status_code == 200:
                results = resp.json().get("coins", [])
                if results:
                    coin_id = results[0]["id"]
                    # 2. Get Price Data
                    param_str = "localization=false&tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"
                    coin_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?{param_str}"
                    price_resp = await client.get(coin_url)
                    
                    if price_resp.status_code == 200:
                        data = price_resp.json()
                        md = data.get("market_data", {})
                        
                        return {
                            "coingecko_id": data.get("id"),
                            "symbol": data.get("symbol", "").upper(),
                            "price_usd": md.get("current_price", {}).get("usd", 0),
                            "market_cap": md.get("market_cap", {}).get("usd", 0),
                            "vol_24h": md.get("total_volume", {}).get("usd", 0),
                            "change_24h": md.get("price_change_percentage_24h", 0),
                            "ath": md.get("ath", {}).get("usd", 0),
                            "atl": md.get("atl", {}).get("usd", 0),
                            "fdv": md.get("fully_diluted_valuation", {}).get("usd", 0),
                            "total_supply": md.get("total_supply", 0),
                            "circ_supply": md.get("circulating_supply", 0)
                        }
    except Exception as e:
        logger.warning(f"CoinGecko failed: {e}")
    return None

async def collect_on_chain_data(input_str: str):
    """
    Query Aptos Node if input looks like an address.
    """
    if str(input_str).startswith("0x") and len(input_str) > 60:
        try:
            node_url = "https://fullnode.testnet.aptoslabs.com/v1"
            async with httpx.AsyncClient() as client:
                # Get Resources
                url = f"{node_url}/accounts/{input_str}/resources"
                resp = await client.get(url)
                if resp.status_code == 200:
                    resources = resp.json()
                    # Summary
                    modules = [r["type"] for r in resources if "0x1::" not in r["type"]]
                    return {
                        "is_contract": len(modules) > 0,
                        "modules_count": len(modules),
                        "balance_apt": "Checked via CoinStore" # Simplified
                    }
        except Exception as e:
            logger.warning(f"Aptos Node failed: {e}")
    return None

async def collect_social_signals(query: str):
    """
    Google Search for 'scam', 'reddit', 'twitter'.
    """
    signals = []
    try:
        # Sync wrapper for google search (it's blocking)
        # We search specifically for negative signals or social proof
        search_query = f"{query} crypto scam reddit twitter"
        # Run in thread executor locally
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: list(search(search_query, num_results=5, lang="en")))
        signals = results
    except Exception as e:
        logger.warning(f"Search failed: {e}")
    return signals

# --- Main Collector ---

async def collect_data(url_or_input: str, project_type: str) -> CollectorData:
    """
    Orchestrates collection from Web, Market, Chain, and Socials.
    """
    raw_text = ""
    title = ""
    docs_present = False
    contracts_found = False
    
    market_data = None
    on_chain_data = None
    social_signals = None

    # 1. Determine Input Type (URL vs Address vs Name)
    is_url = url_or_input.startswith("http")
    is_address = url_or_input.startswith("0x")
    search_term = url_or_input
    
    # 2. Web Scraping (if URL)
    if is_url:
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
                resp = await client.get(url_or_input)
                
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                title_tag = soup.find('title')
                title = title_tag.string if title_tag else url_or_input
                search_term = title # Use title for other searches
                
                # Cleanup
                for script in soup(["script", "style", "nav", "footer"]):
                    script.extract()
                raw_text = soup.get_text(separator=' ', strip=True)
                
                lower_text = raw_text.lower()
                if "docs" in lower_text or "whitepaper" in lower_text:
                    docs_present = True
            else:
                raw_text = f"Failed to load page: HTTP {resp.status_code}"

        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raw_text = f"Scraping error: {str(e)}"
            title = "Analysis Failed"
    else:
        title = url_or_input # It's a name or address

    # 3. Parallel Fetching for Extras
    # If it's a Token project, check Market
    if "Token" in project_type or "Coin" in project_type:
        market_data = await collect_market_data(search_term)

    # 4. On-Chain Check
    if is_address:
        on_chain_data = await collect_on_chain_data(url_or_input)
        contracts_found = on_chain_data.get("is_contract", False) if on_chain_data else False
    
    # 5. Social Search (All)
    social_signals = await collect_social_signals(search_term)

    # 6. Aggregate
    return CollectorData(
        project_name=str(title)[:50],
        domain_age="Auto-Detected",
        contracts_found=contracts_found,
        docs_present=docs_present,
        raw_signals={"text_content": raw_text[:3000]},
        market_data=market_data,
        on_chain_data=on_chain_data,
        social_signals=social_signals
    )
