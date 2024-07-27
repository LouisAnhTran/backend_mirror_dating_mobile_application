from fastapi import FastAPI
from src.api.v1.app import api_router
from src.config import PORT
import logging
from fastapi.middleware.cors import CORSMiddleware
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging
import sys 
import logging_config


app = FastAPI()


# Optionally, add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)

