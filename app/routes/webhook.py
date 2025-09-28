from fastapi import APIRouter, Request, Response, HTTPException
import hmac
import hashlib
import json
from datetime import datetime

router = APIRouter()


def verify_signature(secret: str, signature: str, body: bytes) -> bool:
    mac = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(signature or "", expected)

# webhook by lordphone
@router.post("/webhook", status_code=204)
async def webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    delivery_id = request.headers.get("X-GitHub-Delivery")
    event_type = request.headers.get("X-GitHub-Event", "unknown")
    secret = request.app.state.settings.webhook_secret

    if not verify_signature(secret, signature, body):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse payload to get action for dedupe key
    try:
        payload = json.loads(body.decode('utf-8'))
        action = payload.get("action", "unknown")
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = {}
        action = "unknown"

    # Create dedupe key using delivery ID + action
    dedupe_key = f"{delivery_id}:{action}"

    # Check if already processed (idempotency)
    if dedupe_key in request.app.state.processed_webhooks:
        # Already processed - return 200 for idempotent response
        return Response(status_code=200)

    # Store webhook event for debugging
    event_data = {
        "id": delivery_id,
        "event": event_type,
        "action": action,
        "issue_number": payload.get("issue", {}).get("number") if payload.get("issue") else None,
        "timestamp": datetime.utcnow().isoformat(),
        "payload_size": len(body)
    }

    # Add to storage
    request.app.state.webhook_events.append(event_data)
    request.app.state.processed_webhooks.add(dedupe_key)

    # Keep only last 100 events to prevent memory growth
    if len(request.app.state.webhook_events) > 100:
        request.app.state.webhook_events = request.app.state.webhook_events[-100:]

    return Response(status_code=204)


# get_events by lordphone
@router.get("/events")
async def get_events(request: Request, limit: int = 50):
    """
    Get the last N processed webhook deliveries for debugging.
    Optional endpoint as mentioned in assignment.
    """
    events = request.app.state.webhook_events
    # Return last N events (most recent first)
    limited_events = events[-limit:] if limit > 0 else events
    return list(reversed(limited_events))  # Most recent first
