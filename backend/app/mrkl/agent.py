from abc import ABC, abstractmethod
from typing import List, NamedTuple, Optional, Union

from llm import LLM
from prompt import Prompt, PromptTemplate
from tool import Toolkit


class Action(NamedTuple):
    """Represents an action that an agent takes."""
    tool_name: str
    """The name of the tool used to perform the action."""
    tool_input: str
    """The input given to the tool."""
    log: str
    """The complete output from the LLM that describes this action."""


class FinalAnswer(NamedTuple):
    """Represents the final answer that is reached by an agent after any
    number of actions are taken."""
    output: str
    """The answer itself."""
    log: str
    """The raw output from the LLM that describes the answer."""


class Step(NamedTuple):
    """Represents a step taken in an agent's lifecycle."""
    action: Action
    """The action that was taken."""
    observation: str
    """The observation that was derived during the step. Generally, this is
    the output from a tool."""


class Agent(ABC):
    """An entity that derives an answer to a question by breaking down the
    question into a number of steps and using tools to complete those
    steps."""

    def __init__(
        self,
        llm: LLM,
        prompt_template: PromptTemplate,
        toolkit: Toolkit,
        max_steps: Optional[int] = 15
    ) -> None:
        """Creates a new agent.

          Args:
            llm `LLM`: The language model that will be used for completion.
            prompt_template `PrompTemplate`: An outline for the prompt that
            this agent will use to call the language model.
            toolkit `Toolkit`: A container for the tools that this agent
            can use.
            max_steps `Optional[int]`: The maximum number of steps that this
            agent is allowed to take to answer a question.

          Returns:
            None
        """
        self._llm: LLM = llm
        self._prompt_template: PromptTemplate = prompt_template
        self._toolkit: Toolkit = toolkit
        self._max_steps: int = max_steps
        self._steps: List[Step] = []
        """Stores the steps that have occurred so far in the agent's
        lifecycle"""

    # Properties
    @property
    @abstractmethod
    def _stop(self) -> Union[str, List[str]]:
        """The pattern(s) that the LLM should stop on if they are detected
        in its output."""
        raise NotImplementedError

    @property
    @abstractmethod
    def _observation_prefix(self) -> str:
        """Prefix to append the observation with."""
        raise NotImplementedError

    @property
    @abstractmethod
    def _llm_prefix(self) -> str:
        """Prefix to append the LLM call with."""
        raise NotImplementedError

    # Core methods
    def run(self, query: str) -> str:
        """Starts the agent's lifecycle by giving it an input that is should
        generate an answer for.

            Args:
                query (str): The query that the agent should respond to.

            Returns:
                (str) The derived response to the query.
        """
        while self._should_continue():
            prompt = self._construct_prompt(query)
            llm_output = self._llm.predict(prompt, self._stop)
            action_or_final_answer = self._parse_llm_output(llm_output)
            if isinstance(action_or_final_answer, FinalAnswer):
                final_answer = action_or_final_answer
                print(query + str(self._steps))
                print(final_answer.log)
                return final_answer.output
            action: Action = action_or_final_answer
            tool = self._toolkit.get_tool_by_name(action.tool_name)
            if not tool:
                raise NotImplementedError("Implement proper error handling")
            observation = tool.use(action.tool_input)
            self._steps.append(Step(action=action, observation=observation))
        return "AGENT FINISHED WITHOUT REACHING A FINAL ANSWER"

    # Utility/convenience methods
    @classmethod
    @abstractmethod
    def create_prompt_template(cls, *args, **kwargs) -> PromptTemplate:
        """Create a prompt that conforms to this agent's expectations."""
        raise NotImplementedError

    # Private methods
    @abstractmethod
    def _prepare_for_new_lifecycle(self) -> None:
        """Performs whatever operations are necessary to prep the agent for a
        fresh lifecycle a.k.a. a new call to `self.run`. A default
        implementation is provided by the parent class, but consider whether
        or not this implementation is complete when making a subclass."""
        self._steps = []
        return

    @abstractmethod
    def _should_continue(self) -> bool:
        """Determines whether the agent should continue taking steps. A
        default implementation is provided by the parent class, but consider
        whether or not this implementation is complete when making a
        subclass."""
        return len(self._steps) <= self._max_steps

    @abstractmethod
    def _construct_prompt(self, query: str) -> Prompt:
        """Constructs the prompt for the LLM by formatting
        `self._prompt_template` with the query and its other input variables.
        """
        raise NotImplementedError

    @abstractmethod
    def _parse_llm_output(self, llm_output: str) -> Union[Action, FinalAnswer]:
        """Constructs an `Action` or a `FinalAnswer` from the LLM's output."""
        raise NotImplementedError
