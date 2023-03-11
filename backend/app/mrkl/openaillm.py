import os
from typing import List, Optional, Union

import openai
from llm import LLM
from prompt import Prompt

DEFAULT_MAX_TOKENS = 1000
DEFAULT_TEMPERATURE = 1
DEFAULT_TOP_P = None
DEFAULT_N = 1
DEFAULT_STOP = None


class OpenAILLM(LLM):
    """Abstraction for any of OpenAI's text completion models."""

    def __init__(
        self,
        model: Optional[str] = "text-davinci-003",
        max_tokens: Optional[int] = DEFAULT_MAX_TOKENS,
        temperature: Optional[Union[int, None]] = DEFAULT_TEMPERATURE,
        top_p: Optional[Union[int, None]] = DEFAULT_TOP_P,
        n: Optional[int] = DEFAULT_N,
        stop: Optional[Union[str, List[str], None]] = DEFAULT_STOP,
    ) -> None:
        """Creates an instance for an OpenAI LLM.

            Args:
                `model` `Optional[str]`: The OpenAI model to use.
                `max_tokens` `Optional[int]`: Maximum number of tokens to use.
                `temperature` `Optional[Union[int, None]]`: Temperature of the
                model. High values give more random generations. Lower gives
                more deterministic generations.
                `top_p` `Optional[int]`: Alternative to `temperature`. Use one
                or the other, but not both. Specifies that the model should
                only consider the results of the tokens with the`top_p`
                probability mass.
                `n` `Optional[int]`: How many completions to generate.
                `stop` `Optional[Union[str, List[str]]]`: Up to 4 sequences
                where the LLM will stop generating further tokens; the
                returned completions will not contain the stop sequence.

            Returns:
                `None`
        """
        self._model: str = model
        self._max_tokens: int = max_tokens
        self._temperature: Union[int, None] = temperature
        self._top_p: Union[int, None] = top_p
        self._n: int = n
        self._stop: Union[str, List[str], None] = stop
        try:
            openai.api_key = os.getenv("OPENAI_API_KEY")
        except Exception:
            raise RuntimeError((
                "Failed to connect to OpenAI's sdk. "
                "Make sure that `OPENAI_API_KEY` environment variable is set."
            ))

    def predict(
        self,
        prompt: Prompt,
        stop: Optional[Union[str, List[str], None]] = None
    ) -> str:
        return openai.Completion.create(
            model=self._model,
            prompt=prompt.prompt,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            top_p=self._top_p,
            n=self._n,
            stop=stop if stop else self._stop
        )["choices"][0]["text"]
