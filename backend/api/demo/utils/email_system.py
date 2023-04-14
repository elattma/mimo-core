import re
from abc import ABC
from dataclasses import dataclass
from typing import List
from urllib.parse import quote

import requests
from langchain.agents import AgentExecutor, load_tools, Tool, ZeroShotAgent
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI

PREFIX = '''You are an expert at writing emails. Based on the request from the user, write an email to the best of your ability.
The user will assume you know everything about their company and its customers. Since you don't, use your tools to look up information as needed.
When looking up information, be as descriptive as possible about the information you need. For example, include the sources where the information is located, the time period, or names of people involved, when relevant.
Your Final Answer should always have the following structure:
--------
To: <EMAIL ADDRESS>
Subject: <SUBJECT>
<BODY>
--------

You have access to the following tools:'''

SUFFIX = '''Remember to use your tools when you don't know something.
Do not try to look up two things at once. If you need to know multiple things, use your tools multiple times.
Question: {input}
{agent_scratchpad}'''

INPUT_VARIABLES = ['input', 'agent_scratchpad']

MAX_ITERATIONS = 5

MIMO_DATA_AGENT_TMP_ENDPOINT = 'https://ztsl6igv66ognn6qpvsfict6y40qocst.lambda-url.us-east-1.on.aws'

class EmailSystemResponse(ABC):
    pass

@dataclass
class EmailSystemSuccess(EmailSystemResponse):
    recipient: str
    subject: str
    body: str
    link: str

@dataclass
class EmailSystemError(EmailSystemResponse):
    message: str

class EmailSystem:
    _llm: ChatOpenAI = None
    _tools: List[Tool] = None
    _agent: ZeroShotAgent = None
    _agent_executor: AgentExecutor = None

    def __init__(self,
        openai_api_key: str,
        mimo_test_token: str
    ) -> None:
        self._mimo_test_token = mimo_test_token
        if not self._llm:
            self._llm = ChatOpenAI(
                openai_api_key=openai_api_key,
                temperature=0.2
            )
        if not self._tools:
            math_llm = OpenAI(
                openai_api_key=openai_api_key,
                temperature=0.0
            )
            math_tool = load_tools(tool_names=['llm-math'], llm=math_llm)
            self._tools = self._make_tools() + math_tool
        if not self._agent:
            self._agent = ZeroShotAgent.from_llm_and_tools(
                llm=self._llm,
                tools=self._tools,
                prefix=PREFIX,
                suffix=SUFFIX,
                input_variables=INPUT_VARIABLES
            )
        if not self._agent_executor:
            self._agent_executor = AgentExecutor.from_agent_and_tools(
                self._agent,
                self._tools,
                max_iterations=MAX_ITERATIONS,
                verbose=True
            )
        self._recipients = []
        self._context = ''

    def run(self, message: str) -> EmailSystemResponse:
        try:
            agent_output = self._agent_executor.run(input=message)
            response = self._parse_output(agent_output)
        except Exception as e:
            print(e)
            message = ('Something went wrong. Please try again. It might '
                       'help to rephrase your message.')
            response = EmailSystemError(message)
        return response

    def _make_tools(self) -> List[Tool]:
        data_fetcher = Tool(
            'Context Fetcher',
            self._fetch_context,
            (
                'Used to look up information from the user\'s knowledge base '
                'that you should include in the email. Input should be a '
                'description of what you want to know more about. Output '
                'will be relevant information from the user\'s knowledge '
                'base, if it exists.'
            )
        )
        directory = Tool(
            'Directory',
            self._look_up_email,
            (
                'Used to look up an email address of a person in the user\'s '
                'CRM. Input should be the name of the person. Output will be '
                'a contact from the CRM, if it exists.'
            )
        )
        tools = [
            data_fetcher, directory
        ]
        return tools
    
    def _fetch_context(self, input: str) -> str:
        return _query_mimo_api(input, self._mimo_test_token)

    def _look_up_email(self, input: str) -> str:
        name = input.strip()
        input = f'{name}\'s email address from the CRM'
        return _query_mimo_api(input, self._mimo_test_token)
    
    def _parse_output(self, output: str) -> EmailSystemResponse:
        recipient_match = re.search(r'To:(.*)', output)
        recipient = recipient_match.group(1).strip() if recipient_match else None
        subject_match = re.search(r'Subject:(.*)', output)
        subject = subject_match.group(1).strip() if subject_match else None
        body_match = re.search(r'Subject:.*\n([\s\S]*)', output)
        body = body_match.group(1).strip() if body_match else None
        link = 'mailto:'
        if recipient:
            link += quote(recipient)
        link += '?'
        if subject:
            link += f'subject={quote(subject)}'
        if body:
            if subject:
                link += '&'
            link += f'body={quote(body)}'
        return EmailSystemSuccess(recipient, subject, body, link)
    
def _query_mimo_api(message: str, mimo_test_token: str) -> str:
    response = requests.get(MIMO_DATA_AGENT_TMP_ENDPOINT, params={
            'question': message,
            'test_token': mimo_test_token
        }
    )
    response = response.json() if response else None
    answer = response.get('answer', None) if response else None
    return answer