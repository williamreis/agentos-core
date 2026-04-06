from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Contrato mínimo: recebe texto e devolve texto (ex.: JSON serializado)."""

    name: str = "base"

    @abstractmethod
    def run(self, user_input: str) -> str:
        raise NotImplementedError
