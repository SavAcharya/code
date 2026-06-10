import abc
import logging

logger = logging.getLogger(__name__)


class LLMProvider(abc.ABC):
    name: str
    model: str

    @abc.abstractmethod
    async def generate(self, system: str, prompt: str, temperature: float = 0.1) -> str:
        ...

    @abc.abstractmethod
    async def health_check(self) -> bool:
        ...

    def model_id(self) -> str:
        return f"{self.name}/{self.model}"
