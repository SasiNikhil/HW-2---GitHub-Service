import os 
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .routes import issues, comments, webhook

app = FastAPI(default_response_class=ORJSONResponse)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=False, allow_methods=['*'], allow_headers=['*'])

@app.on_event('startup')
async def startup():
    app.state.settings = get_settings()

@app.get('/healthz')
async def healthz():
    return {'status': 'ok'}

app.include_router(issues.router)
app.include_router(comments.router)
app.include_router(webhook.router)
