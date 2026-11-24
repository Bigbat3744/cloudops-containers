import os
import socket
from datetime import datetime, timezone

from fastapi import FastAPI

app = FastAPI(title="cloudops-containers")
VERSION = os.getenv("APP_VERSION", "dev")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {
        "service": "cloudops-containers",
        "version": VERSION,
        "host": socket.gethostname(),
        "time": datetime.now(timezone.utc).isoformat(),
    }
