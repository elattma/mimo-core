from typing import Callable, Dict, List, Optional, Union


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        parser: Optional[Callable] = None
    ) -> None:
        """Creates a new tool.

            Args:
                `name` `str`: The name of the tool.
                `description` `str`: What the tool does. It is helpful to
                include what the input should look like and what the output
                will look like.
                `func` `Callable`: The function that the tool calls when it
                is used.
                `parser` `Optional[Union[Callable, None]]`: An optional helper
                function that can transform the LLM's output (`str`) to the
                form that `func` expects. This must be defined if `func`
                expects anything but a `str` as input.

            Returns:
                `None`
        """
        self._name = name
        self._description = description
        self._func = func
        self._parser = parser

    @property
    def name(self) -> str:
        """The name of the tool."""
        return self._name

    @property
    def description(self) -> str:
        """A description of the tool."""
        return self._description

    def use(self, tool_input: str) -> str:
        """Uses the tool on an input.

            Args:
                `tool_input` `str`: The input to the tool that has been parsed
                from an LLM's response.

            Returns:
                `str` The result of using the tool on the specified input.
        """
        if self._parser is None:
            return self._func(tool_input)
        else:
            return self._func(self._parser(tool_input))


class Toolkit:
    """A collection of tools that an agent can use."""

    def __init__(self, tools: List[Tool]) -> None:
        """Creates a new toolkit.

            Args:
                tools (List[Tool]): The tools to store in this toolkit.

            Returns:
                `None`
        """
        self._tools: List[Tool] = tools
        self._names: List[str] = [tool.name for tool in tools]
        self._lookup: Dict[str, Tool] = {
            tool.name: tool for tool in tools
        }

    @property
    def tools(self) -> List[Tool]:
        """The tools in the toolkit."""
        return self._tools

    @property
    def names(self) -> List[str]:
        """The names of the tools in the toolkit."""
        return self._names

    def get_tool_by_name(self, name: str) -> Union[Tool, None]:
        """Finds the tool in the toolkit with the matching name.

            Args:
                `name` `str`: The name of the tool to find.

            Returns:
                `Union[Tool, None]` The tool if it exists in the toolkit,
                otherwise nothing.
        """
        return self._lookup[name] if name in self._lookup else None
