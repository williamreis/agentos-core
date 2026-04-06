from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=16_000, description="Texto de entrada para o agente")
