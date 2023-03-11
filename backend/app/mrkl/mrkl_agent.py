import re
from typing import List, Optional, Union

from agent import Action, Agent, FinalAnswer
from llm import LLM
from prompt import Prompt, PromptTemplate
from tool import Toolkit

DEFAULT_PREFIX = (
    "Answer the following questions to the best of your ability. You have "
    "access to the following tools:"
)
DEFAULT_FORMAT_INSTRUCTIONS = """Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question"""
DEFAULT_SUFFIX = """Begin!

Question: {query}
Thought: {scratchpad}"""
DEFAULT_INPUT_VARIABLES = ["query", "scratchpad"]

FINAL_ANSWER_PATTERN = "Final Answer:"

DEFAULT_MAX_STEPS = 10


class MRKLAgent(Agent):
    """An agent that emulates a router from the MRKL System.
    https://arxiv.org/pdf/2205.00445.pdf"""

    def __init__(
        self,
        llm: LLM,
        toolkit: Toolkit,
        prompt_template: Optional[Union[PromptTemplate, None]] = None,
        max_steps: Optional[int] = DEFAULT_MAX_STEPS
    ) -> None:
        if prompt_template is None:
            prompt_template = MRKLAgent.create_prompt_template(toolkit)
        super().__init__(llm, prompt_template, toolkit, max_steps=max_steps)

    # Properties
    @property
    def _stop(self) -> List[str]:
        return [
            f"\n{self._observation_prefix}",
            f"\n\t{self._observation_prefix}"
        ]

    @property
    def _observation_prefix(self) -> str:
        return "Observation: "

    @property
    def _llm_prefix(self) -> str:
        return "Thought:"

    @property
    def _scratchpad(self) -> str:
        """A place for the agent to keep track of its past actions."""
        thoughts = ""
        for action, observation in self._steps:
            thoughts += action.log
            thoughts += f"\n{self._observation_prefix}{observation}"
            thoughts += f"\n{self._llm_prefix}"
        return thoughts

    # Utility/convenience methods
    @classmethod
    def create_prompt_template(
        cls,
        toolkit: Toolkit,
        prefix: Optional[str] = DEFAULT_PREFIX,
        format_instructions: Optional[str] = DEFAULT_FORMAT_INSTRUCTIONS,
        suffix: Optional[str] = DEFAULT_SUFFIX,
        input_variables: Optional[str] = DEFAULT_INPUT_VARIABLES,
    ) -> PromptTemplate:
        tool_descriptions = "\n".join(
            [f"{tool.name}: {tool.description}" for tool in toolkit.tools]
        )
        tool_names = ", ".join(toolkit.names)
        formatted_format_instructions = format_instructions.format(
            tool_names=tool_names
        )
        return PromptTemplate(
            "\n\n".join(
                [
                    prefix,
                    tool_descriptions,
                    formatted_format_instructions,
                    suffix
                ],
            ),
            input_variables
        )

    # Private methods
    def _prepare_for_new_lifecycle(self) -> None:
        super()._prepare_for_new_lifecycle()

    def _should_continue(self) -> bool:
        return super()._should_continue()

    def _construct_prompt(self, query: str) -> Prompt:
        scratchpad = self._scratchpad
        inputs = {
            "scratchpad": scratchpad,
            "query": query
        }
        return self._prompt_template.create_prompt_from_template(inputs)

    def _parse_llm_output(
        self,
        llm_output: str
    ) -> Union[Action, FinalAnswer]:
        if FINAL_ANSWER_PATTERN in llm_output:
            output = llm_output.split(FINAL_ANSWER_PATTERN)[-1].strip()
            return FinalAnswer(output=output, log=llm_output)
        pattern = r"Action: (.*?)[\n]*Action Input: (.*)"
        match = re.search(pattern, llm_output, re.DOTALL)
        tool_name = match.group(1).strip()
        tool_input = match.group(2).strip(" ").strip('"')
        if not tool_name or not tool_input:
            raise ValueError(
                "`MRKLAgent._parse_llm_output`: Couldn't parse LLM output" +
                llm_output
            )
        return Action(
            tool_name=tool_name,
            tool_input=tool_input,
            log=llm_output
        )
