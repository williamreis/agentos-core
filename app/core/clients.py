from __future__ import annotations
from app.agents.faq.agent import FAQAgent
from app.agents.fraud.agent import FraudAgent


class FraudClient:
    def __init__(self) -> None:
        self._agent = FraudAgent()

    def run(self, user_input: str) -> str:
        return self._agent.run(user_input)


class FAQClient:
    def __init__(self) -> None:
        self._agent = FAQAgent()

    def run(self, user_input: str) -> str:
        return self._agent.run(user_input)
