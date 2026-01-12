import httpx

from config import settings


TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile(token: str | None) -> bool:
    """
    verify a Cloudflare Turnstile token
    """
    # skip verification if Turnstile is not configured
    if not settings.TURNSTILE_SECRET_KEY:
        return True
    
    # require token if Turnstile is configured
    if not token:
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TURNSTILE_VERIFY_URL,
                data={
                    "secret": settings.TURNSTILE_SECRET_KEY,
                    "response": token,
                },
                timeout=10
            )
            
            result = response.json()
            return result.get("success", False)
            
    except Exception:
        # fail closed - if verification fails, reject the request
        return False
