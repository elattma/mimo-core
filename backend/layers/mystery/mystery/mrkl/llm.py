from abc import ABC, abstractmethod
from typing import List, Optional, Union

from .prompt import Prompt


class LLM(ABC):
    @abstractmethod
    def predict(
        self,
        prompt: Prompt,
        stop: Optional[Union[str, List[str]]]
    ) -> str:
        """Runs a completion using the instance's model.

            Args:
                `prompt` `Prompt`: The prompt to call the LLM with.
                `stop` `Optional[Union[str, List[str]]]`: A custom stop or set
                of stop keywords to override `self._stop`.

            Returns:
                `str` The LLM's completion for the given prompt.
        """
        raise NotImplementedError("LLM: predict not implemented")
