# Coded by Dev Mulchandani
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .routes import issues, comments, webhook

app = FastAPI(default_response_class=ORJSONResponse)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=False, allow_methods=['*'], allow_headers=['*'])

# startup by lordphone
@app.on_event('startup')
async def startup():
    app.state.settings = get_settings()
    # Initialize webhook storage for idempotency
    app.state.processed_webhooks = set()
    app.state.webhook_events = []
    # Initialize ETag cache for conditional GET
    app.state.etag_cache = {}


@app.get('/healthz')
async def healthz():
    return {'status': 'ok'}

app.include_router(issues.router)
app.include_router(comments.router)
app.include_router(webhook.router)
