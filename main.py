from fastapi import FastAPI
import logging
from fastapi.middleware.cors import CORSMiddleware
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging
import sys 
import logging_config

from src.config import (
    PORT,
    API_VERSION)

if API_VERSION=="1":
    from src.api.v1.auth.router import api_router as api_router_auth
    from src.api.v1.pdf_query.router import api_router as api_router_pdf_query
    from src.api.v1.ai_benchmarking.router import api_router as api_router_ai_benchmarking
    from src.api.v1.ai_catalogue.router import api_router as api_router_ai_catalogue
else:
    from src.api.v2.auth.router import api_router as api_router_auth
    from src.api.v2.pdf_query.router import api_router as api_router_pdf_query
    from src.api.v2.ai_benchmarking.router import api_router as api_router_ai_benchmarking
    from src.api.v2.ai_catalogue.router import api_router as api_router_ai_catalogue

app = FastAPI()


# Optionally, add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX=f"/api/v{API_VERSION}/"
app.include_router(api_router_auth, prefix=f"{PREFIX}auth")
app.include_router(api_router_ai_catalogue,prefix=f"{PREFIX}ai_catalogue")
app.include_router(api_router_ai_benchmarking,prefix=f"{PREFIX}ai_benchmarking")
app.include_router(api_router_pdf_query,prefix=f"{PREFIX}pdf_query")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)

