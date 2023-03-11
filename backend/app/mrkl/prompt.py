from typing import Dict, List


class Prompt:
    """An LLM-ready prompt."""

    def __init__(self, prompt: str) -> None:
        self._prompt: str = prompt

    @property
    def prompt(self) -> str:
        return self._prompt


class PromptTemplate:
    """The outline of a prompt for an LLM."""

    def __init__(self, template: str, input_variables: List[str]) -> None:
        self._template: str = template
        self._input_variables: List[str] = input_variables

    @property
    def template(self) -> str:
        """The template."""
        return self._template

    @property
    def input_variables(self) -> List[str]:
        """The variables that exist in the template."""
        return self._input_variables

    def create_prompt_from_template(self, inputs: Dict[str, str]) -> Prompt:
        """Create a prompt from the prompt template by supplying values for
        the input variables.

            Args:
                inputs (`Dict[str, str]`): The values to assign to
                `input_variables` keyed by the variable names.

            Returns:
                (`Prompt`) A formatted prompt.
        """
        self._validate_inputs(inputs)
        return Prompt(self._template.format(**inputs))

    def _validate_inputs(self, inputs: Dict[str, str]) -> None:
        """Enforces that a value is provided for every variable in the
        template."""
        if not set(inputs.keys()) == set(self._input_variables):
            raise ValueError((
                "`PromptTemplate._validate_inputs`: keys from `inputs` do "
                "not match the elements in `self._input_variables`."
            ))
