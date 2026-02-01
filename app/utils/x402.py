import httpx
import logging

logger = logging.getLogger(__name__)

# Basic logging config if not already set
logging.basicConfig(level=logging.INFO)

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
        logger.info(f"Verifying Tx {tx_hash} payload: {payload}")
        
        # 2. Check function (Coin transfer or AptosAccount transfer)
        func = payload.get("function", "")
        if "0x1::coin::transfer" not in func and "0x1::aptos_account::transfer" not in func:
            logger.warning(f"Tx {tx_hash} incorrect function: {func}")
            return False
            
        args = payload.get("arguments", [])
        if len(args) < 2:
            logger.warning(f"Tx {tx_hash} insufficient arguments: {args}")
            return False
            
        recipient = args[0]
        try:
            amount = int(args[1])
        except (ValueError, TypeError):
            logger.warning(f"Tx {tx_hash} invalid amount argument: {args[1]}")
            return False
        
        logger.info(f"Tx {tx_hash} parsed: recipient={recipient}, amount={amount}")
        
        # 3. Verify Recipient and Amount
        # Normalize addresses (0x prefixed, lowercase)
        norm_recipient = recipient.lower() if recipient.startswith("0x") else f"0x{recipient.lower()}"
        norm_target = PAYMENT_RECIPIENT.lower()
        
        if norm_recipient != norm_target:
            logger.warning(f"Tx {tx_hash} recipient mismatch. Got {norm_recipient}, needed {norm_target}")
            return False
            
        if amount < REQUIRED_AMOUNT_OCTAS:
            logger.warning(f"Tx {tx_hash} insufficient amount. Got {amount}, needed {REQUIRED_AMOUNT_OCTAS}")
            return False
            
        logger.info(f"Tx {tx_hash} verified successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error verifying tx {tx_hash}: {e}")
        return False
