from typing import List

import requests
from langchain.agents import AgentExecutor, Tool, ZeroShotAgent, load_tools
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI

from . import constants
from .model import EmailSystemError, EmailSystemResponse


class EmailSystem:
    def __init__(self,
        openai_api_key: str,
        mimo_test_token: str
    ) -> None:
        self._openai_api_key = openai_api_key
        self._mimo_test_token = mimo_test_token
        self._llm = ChatOpenAI(openai_api_key=openai_api_key, temperature=0.0)
        self._tools = self._make_tools()
        self._agent = ZeroShotAgent.from_llm_and_tools(
            self._llm,
            self._tools,
            prefix=constants.PREFIX,
            suffix=constants.SUFFIX,
            input_variables=constants.INPUT_VARIABLES
        )
        self._agent_executor = AgentExecutor.from_agent_and_tools(
            self._agent,
            self._tools,
            max_iterations=constants.MAX_ITERATIONS,
            verbose=True
        )

    def run(self, message: str) -> EmailSystemResponse:
        try:
            agent_output = self._agent_executor.run(input=message)
        except Exception as e:
            print(e)
            message = ('Something went wrong. Please try again. It might '
                       'help to rephrase your message.')
            return EmailSystemError(message)
        return EmailSystemResponse.from_agent_output(agent_output)

    def _make_tools(self) -> List[Tool]:
        context_fetcher = Tool(
            'Context Fetcher',
            self._fetch_context,
            constants.CONTEXT_FETCHER_DESCRIPTION
        )
        directory = Tool(
            'Directory',
            self._look_up_email,
            constants.DIRECTORY_DESCRIPTION
        )
        llm = OpenAI(openai_api_key=self._openai_api_key, temperature=0.0)
        math = load_tools(tool_names=['llm-math'], llm=llm)[0]
        tools = [context_fetcher, directory, math]
        return tools
    
    def _fetch_context(self, input: str) -> str:
        return _query_mimo_api(input, self._mimo_test_token)

    def _look_up_email(self, input: str) -> str:
        name = input.strip()
        input = f'{name}\'s email address from the CRM'
        return _query_mimo_api(input, self._mimo_test_token)
    

def _query_mimo_api(message: str, mimo_test_token: str) -> str:
    params = {
        'question': message,
        'test_token': mimo_test_token,
        'max_tokens': 100
    }
    response = requests.get(constants.MIMO_ENDPOINT, params=params)
    response = response.json() if response else None
    answer = response.get('answer', None) if response else None
    return answer