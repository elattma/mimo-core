from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class Prompt(ABC):
    """Abstract class for an LLM-ready prompt."""

    @property
    @abstractmethod
    def prompt(self) -> Any:
        raise NotImplementedError("Prompt: prompt not implemented")


class TextPrompt(Prompt):
    """An LLM-ready prompt for text completion, e.g. `text-davinci-003`."""

    def __init__(self, text: str):
        self._text = text

    @property
    def prompt(self) -> str:
        return self._text


class ChatPromptMessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    
@dataclass
class ChatPromptMessage:
    role: ChatPromptMessageRole
    """Who sent the message."""
    content: str
    """The message itself."""


class ChatPrompt(Prompt):
    """An LLM-ready prompt for chat completion, e.g. `gpt-3.5-turbo`."""
    def __init__(self, messages: List[ChatPromptMessage]):
        self._messages = messages
    
    @property
    def prompt(self) -> List[ChatPromptMessage]:
        return self._messages



class PromptTemplate(ABC):
    """Abtract class for the outline of a `Prompt`."""

    @property
    @abstractmethod
    def template(self) -> Any:
        """The template."""
        raise NotImplementedError("PromptTemplate: template not implemented.")

    @property
    @abstractmethod
    def input_variables(self) -> Any:
        """The variables that exist in the template."""
        raise NotImplementedError(
            "PromptTemplate: input_variables not implemented."
        )

    @abstractmethod
    def create_prompt_from_template(self, inputs: Dict[str, str]) -> Prompt:
        """Create a prompt from the prompt template by supplying values for
        the input variables.

            Args:
                inputs (`Dict[str, str]`): The values to assign to
                `input_variables` keyed by the variable names.

            Returns:
                (`Prompt`) A formatted prompt.
        """
        raise NotImplementedError

    def _validate_inputs(self, inputs: Dict[str, str]) -> None:
        """Enforces that a value is provided for every variable in the
        template."""
        if not set(inputs.keys()) == set(self._input_variables):
            raise ValueError((
                "`PromptTemplate._validate_inputs`: keys from `inputs` do "
                "not match the elements in `self._input_variables`."
            ))

class TextPromptTemplate(PromptTemplate):
    """Outline for a `TextPrompt`."""

    def __init__(self, template: str, input_variables: List[str]) -> None:
        self._template: str = template
        self._input_variables: List[str] = input_variables

    @property
    def template(self) -> str:
        return self._template
    
    @property
    def input_variables(self) -> List[str]:
        return self._input_variables

    def create_prompt_from_template(
        self,
        inputs: Dict[str, str]
    ) -> TextPrompt:
        self._validate_inputs(inputs)
        return TextPrompt(self._template.format(**inputs))
    

class ChatPromptTemplate(PromptTemplate):
    """Outline for a `ChatPrompt`."""

    def __init__(
        self,
        template: List[ChatPromptMessage],
        input_variables: List[str]
    ) -> None:
        self._template: List[ChatPromptMessage] = template
        self._input_variables: List[str] = input_variables

    @property
    def template(self) -> List[ChatPromptMessage]:
        return self._template
    
    @property
    def input_variables(self) -> List[str]:
        return self._input_variables
    
    def create_prompt_from_template(
        self,
        inputs: Dict[str, str]
    ) -> ChatPrompt:
        self._validate_inputs(inputs)
        messages = [
            ChatPromptMessage(
                role=message.role,
                content=message.content.format(**inputs)
            ) for message in self._template
        ]
        return ChatPrompt(messages=messages)