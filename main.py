from __future__ import annotations
from fastapi import Depends, FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.core.executor import run_agent
from app.core.registry import AGENT_MANIFEST
from app.models.schemas import AgentRequest
from app.shared.auth.auth import require_agent_access

app = FastAPI(
    title="AgentOS Core",
    description="Orquestração de agentes",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "auth_enabled": get_settings().auth_enabled,
    }


@app.get("/agents")
def list_agents():
    return {"agents": AGENT_MANIFEST}


@app.post("/agent/fraud")
def post_fraud(
        body: AgentRequest,
        _auth: str = Depends(require_agent_access("fraud")),
        x_app_id: str | None = Header(default=None, alias="X-App-Id"),
):
    return run_agent("fraud", body.input, app_id=x_app_id)


@app.post("/agent/faq")
def post_faq(
        body: AgentRequest,
        _auth: str = Depends(require_agent_access("faq")),
        x_app_id: str | None = Header(default=None, alias="X-App-Id"),
):
    return run_agent("faq", body.input, app_id=x_app_id)
