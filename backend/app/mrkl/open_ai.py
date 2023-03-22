from abc import ABC, abstractmethod
from typing import Generator, List, Optional, Union

from app.client._openai import OpenAI
from app.mrkl.llm import LLM
from app.mrkl.prompt import ChatPrompt, Prompt, TextPrompt

DEFAULT_TEXT_MODEL = 'text-davinci-003'
DEFAULT_CHAT_MODEL = 'gpt-3.5-turbo'
DEFAULT_MAX_TOKENS = 1000
DEFAULT_TEMPERATURE = 0
DEFAULT_TOP_P = None
DEFAULT_N = 1
DEFAULT_STOP = None


class OpenAIBase(LLM, ABC):
    '''Abstract class for OpenAI's completion models.'''

    def __init__(
        self,
        client: OpenAI,
        model: Optional[str] = None,
        max_tokens: Optional[int] = DEFAULT_MAX_TOKENS,
        temperature: Optional[int] = DEFAULT_TEMPERATURE,
        top_p: Optional[int] = DEFAULT_TOP_P,
        n: Optional[int] = DEFAULT_N,
        stop: Optional[Union[str, List[str]]] = DEFAULT_STOP,
    ) -> None:
        '''Creates an instance for an OpenAI LLM.

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
        '''
        self._client = client
        self._model: str = model
        self._max_tokens: int = max_tokens
        self._temperature: Union[int, None] = temperature
        self._top_p: Union[int, None] = top_p
        self._n: int = n
        self._stop: Union[str, List[str], None] = stop

    @property
    @abstractmethod
    def encoding_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def predict(
        self,
        prompt: Prompt,
        stop: Optional[Union[str, List[str]]] = None
    ) -> str:
        super().predict(prompt, stop)


class OpenAIText(OpenAIBase):
    '''Interfaces with any of OpenAI's text completion models.'''

    def __init__(
        self,
        client: OpenAI,
        model: Optional[str] = DEFAULT_TEXT_MODEL,
        max_tokens: Optional[int] = DEFAULT_MAX_TOKENS,
        temperature: Optional[int] = DEFAULT_TEMPERATURE,
        top_p: Optional[int] = DEFAULT_TOP_P,
        n: Optional[int] = DEFAULT_N,
        stop: Optional[Union[str, List[str]]] = DEFAULT_STOP,
    ) -> None:
        super().__init__(
            client=client,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            n=n,
            stop=stop
        )

    @property
    def encoding_name(self) -> str:
        if self._model == 'text-davinci-003':
            return 'p50k_base'
        else:
            raise NotImplementedError

    def predict(
        self,
        prompt: TextPrompt,
        stop: Optional[Union[str, List[str]]] = None
    ) -> str:
        return self._client.completion(
            prompt=prompt.prompt,
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            top_p=self._top_p,
            n=self._n,
            stop=stop if stop else self._stop
        )


class OpenAIChat(OpenAIBase):
    '''Interfaces with any of OpenAI's chat completion models.'''

    def __init__(
        self,
        client: OpenAI,
        model: Optional[str] = DEFAULT_CHAT_MODEL,
        max_tokens: Optional[int] = DEFAULT_MAX_TOKENS,
        temperature: Optional[int] = DEFAULT_TEMPERATURE,
        top_p: Optional[int] = DEFAULT_TOP_P,
        n: Optional[int] = DEFAULT_N,
        stop: Optional[Union[str, List[str]]] = DEFAULT_STOP,
    ) -> None:
        super().__init__(
            client=client,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            n=n,
            stop=stop
        )

    @property
    def encoding_name(self) -> str:
        if self._model == 'gpt-3.5-turbo' or self._model == 'gpt-4':
            return 'cl100k_base'
        else:
            raise NotImplementedError

    def predict(
        self,
        prompt: ChatPrompt,
        stop: Optional[Union[str, List[str]]] = None
    ) -> str:
        messages = [
            {
                'role': message.role,
                'content': message.content
            } for message in prompt.prompt
        ]
        return self._client.chat_completion(
            messages=messages,
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            top_p=self._top_p,
            n=self._n,
            stop=stop if stop else self._stop
        )

    def stream_predict(
        self,
        prompt: ChatPrompt,
        stop: Optional[Union[str, List[str]]] = None
    ) -> Generator:
        messages = [
            {
                'role': message.role,
                'content': message.content
            } for message in prompt.prompt
        ]
        yield from self._client.stream_chat_completion(
            messages=messages,
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            top_p=self._top_p,
            n=self._n,
            stop=stop if stop else self._stop,
        )