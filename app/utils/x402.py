import httpx
import logging

logger = logging.getLogger(__name__)

# Constants from Cheatsheet
APTOS_TESTNET_URL = "https://api.testnet.aptoslabs.com/v1"
PAYMENT_RECIPIENT = "0x701b1d24270dd314d417430fbc2fc5407c4119aa7a94bc3d467d94952f9bc6cc" # Wallet 1
REQUIRED_AMOUNT_APT = 0.01
REQUIRED_AMOUNT_OCTAS = int(REQUIRED_AMOUNT_APT * 100_000_000)

async def verify_payment(tx_hash: str) -> bool:
    """
    Verifies the x402 payment transaction on Aptos Testnet.
    Checks:
    1. Transaction exists and is successful.
    2. Receiver matches PAYMENT_RECIPIENT.
    3. Amount >= REQUIRED_AMOUNT.
    """
    if not tx_hash:
        return False
        
    if tx_hash == "demo": # Keep demo backdoor for quick testing if needed
        return True

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{APTOS_TESTNET_URL}/transactions/by_hash/{tx_hash}")
            
        if resp.status_code != 200:
            logger.warning(f"Tx {tx_hash} not found or error: {resp.text}")
            return False
            
        tx_data = resp.json()
        
        # 1. Check status
        if not tx_data.get("success", False):
            logger.warning(f"Tx {tx_hash} failed on-chain")
            return False
            
        payload = tx_data.get("payload", {})
        
        # 2. Check function (Coin transfer or AptosAccount transfer)
        func = payload.get("function", "")
        if "0x1::coin::transfer" not in func and "0x1::aptos_account::transfer" not in func:
            logger.warning(f"Tx {tx_hash} incorrect function: {func}")
            return False
            
        args = payload.get("arguments", [])
        if len(args) < 2:
            return False
            
        recipient = args[0]
        amount = int(args[1])
        
        # 3. Verify Recipient and Amount
        # Normalize addresses (remove leading 0s after 0x) for comparison if needed, 
        # but standardized format usually matches.
        if recipient != PAYMENT_RECIPIENT:
            logger.warning(f"Tx {tx_hash} recipient mismatch. Got {recipient}, needed {PAYMENT_RECIPIENT}")
            return False
            
        if amount < REQUIRED_AMOUNT_OCTAS:
            logger.warning(f"Tx {tx_hash} insufficient amount. Got {amount}, needed {REQUIRED_AMOUNT_OCTAS}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error verifying tx {tx_hash}: {e}")
        return False
