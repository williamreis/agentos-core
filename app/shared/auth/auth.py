from __future__ import annotations
from fastapi import Header, HTTPException, status
from app.config import get_settings


def _parse_api_key(authorization: str) -> str:
    raw = authorization.strip()
    low = raw.lower()
    if low.startswith("bearer "):
        return raw.split(" ", 1)[1].strip()
    return raw


def _key_to_agent(api_key: str) -> str | None:
    s = get_settings()
    if api_key == s.fraud_api_key:
        return "fraud"
    if api_key == s.faq_api_key:
        return "faq"
    return None


def require_agent_access(allowed_agent: str):
    def _dep(
            authorization: str | None = Header(
                default=None,
                alias="Authorization",
                description=(
                        "Se AUTH_ENABLED=true: chave igual a FRAUD_API_KEY / FAQ_API_KEY ou `Bearer <chave>`. "
                        "Com AUTH_ENABLED=false, pode ser omitido."
                ),
            ),
    ) -> str:
        if not get_settings().auth_enabled:
            return allowed_agent
        if not authorization or not authorization.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization obrigatório (AUTH_ENABLED=true)",
            )
        token = _parse_api_key(authorization)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Chave vazia em Authorization",
            )
        granted = _key_to_agent(token)
        if granted is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Chave inválida",
            )
        if granted != allowed_agent:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Esta chave não pode executar o agente '{allowed_agent}'",
            )
        return granted

    return _dep
