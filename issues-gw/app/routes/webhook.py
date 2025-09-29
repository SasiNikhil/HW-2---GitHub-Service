"""
Mikkilineni Sasi Nikhil
"""
from fastapi import APIRouter, Request, Response, HTTPException
import hmac, hashlib

router = APIRouter()

def verify_signature(secret: str, signature: str, body: bytes) -> bool:
    mac = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(signature or "", expected)

@router.post("/webhook", status_code=204)
async def webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    secret = request.app.state.settings.webhook_secret

    if not verify_signature(secret, signature, body):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Don’t care what event it is (ping, issues, issue_comment, etc.)
    # If signature matches → ACK 204
    return Response(status_code=204)
