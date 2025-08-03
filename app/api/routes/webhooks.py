import hmac
import hashlib
import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse

from app.config import settings
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks")
logger = logging.getLogger(__name__)


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify that the webhook payload was sent by GitHub."""
    if not signature:
        return False
    
    # GitHub sends the signature as 'sha256=<hash>'
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    expected_signature = f"sha256={expected_signature}"
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature, expected_signature)


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
) -> JSONResponse:
    """Handle GitHub webhook events."""
    try:
        # Get the raw payload
        payload = await request.body()
        
        # Verify the webhook signature
        if not verify_webhook_signature(payload, x_hub_signature_256, settings.GITHUB_WEBHOOK_SECRET):
            logger.warning(f"Invalid webhook signature for event: {x_github_event}")
            raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Parse the JSON payload
        try:
            data = json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook payload")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        logger.info(f"Received GitHub webhook event: {x_github_event}")
        
        # Initialize webhook service
        webhook_service = WebhookService()
        
        # Process the webhook event
        result = await webhook_service.process_event(x_github_event, data)
        
        if result:
            logger.info(f"Successfully processed {x_github_event} event")
            return JSONResponse({"status": "success", "message": f"Processed {x_github_event} event"})
        else:
            logger.info(f"Event {x_github_event} was ignored (not relevant)")
            return JSONResponse({"status": "ignored", "message": f"Event {x_github_event} was ignored"})
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/github/ping")
async def webhook_ping():
    """Health check endpoint for webhook."""
    return {"status": "ok", "message": "Webhook endpoint is active"}