import re
from dataclasses import dataclass
from typing import List
from urllib.parse import quote

import requests
from langchain import LLMChain
from langchain.agents import AgentExecutor, Tool, ZeroShotAgent
from langchain.chat_models import ChatOpenAI

PREFIX = '''You are an expert at writing emails. Based on the request from the user, write an email to the best of your ability.
The user will assume you know everything about their company and its customers. Since you don't, use the tools you have access to to look up information you don't know.
Your final answer should be in the following form.
--------
To: <EMAIL ADDRESS>
Subject: <SUBJECT>
<BODY>
--------

You have access to the following tools:'''

SUFFIX = '''Remember to use your tools when you don't know something.
Question: {input}
{agent_scratchpad}'''

INPUT_VARIABLES = ['input', 'agent_scratchpad']

MIMO_DATA_AGENT_TMP_ENDPOINT = 'https://ztsl6igv66ognn6qpvsfict6y40qocst.lambda-url.us-east-1.on.aws'

@dataclass
class EmailSystemResponse:
    recipient: str
    subject: str
    body: str
    link: str

class EmailSystem:
    _llm: ChatOpenAI = None
    _llm_chain: LLMChain = None
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
            self._tools = self._make_tools()
        if not self._llm_chain:
            prompt = ZeroShotAgent.create_prompt(
                self._tools,
                prefix=PREFIX,
                suffix=SUFFIX,
                input_variables=INPUT_VARIABLES
            )
            self._llm_chain = LLMChain(llm=self._llm, prompt=prompt)
        if not self._agent:
            tool_names = [tool.name for tool in self._tools]
            self._agent = ZeroShotAgent(
                llm_chain=self._llm_chain,
                allowed_tools=tool_names
            )
        if not self._agent_executor:
            self._agent_executor = AgentExecutor.from_agent_and_tools(
                self._agent,
                self._tools,
                verbose=True
            )
        self._recipients = []
        self._context = ''

    def run(self, message: str) -> EmailSystemResponse:
        agent_output = self._agent_executor.run(input=message)
        response = self._parse_output(agent_output)
        return response

    def _make_tools(self) -> List[Tool]:
        data_fetcher = Tool(
            'Context Fetcher',
            self._fetch_context,
            ('Used to look up information that the user would like to '
             'include in the email, but you do not know enough about. For '
             'example, if the user wants you to write an email about the '
             'upcoming offsite, you can use this tool to look up the details '
             'of the offsite. Input should be a description of what you want '
             'to know more about. Output will be the information you need.')
        )
        directory = Tool(
            'Directory',
            self._look_up_email,
            ('Used to look up an email address of a person. Input should be '
             'the name of the person. Output will be the email address, if '
             'it exists.')
        )
        tools = [
            data_fetcher, directory
        ]
        return tools
    
    def _fetch_context(self, input: str) -> str:
        return _query_mimo_api(input, self._mimo_test_token)

    def _look_up_email(self, input: str) -> str:
        name = input.strip()
        input = f'What is the email of {name} from the CRM?'
        return _query_mimo_api(input, self._mimo_test_token)
    
    def _parse_output(self, output: str) -> EmailSystemResponse:
        recipient_match = re.search(r'To:(.*)', output).group(1)
        subject_match = re.search(r'Subject:(.*)', output).group(1)
        body_match = re.search(r'Subject:.*\n([\s\S]*)', output).group(1)
        recipient = recipient_match.strip()
        subject = subject_match.strip()
        body = body_match.strip()
        link = quote(f'mailto:{recipient}?subject={subject}&body={body}')
        return EmailSystemResponse(recipient, subject, body, link)
    
def _query_mimo_api(message: str, mimo_test_token: str) -> str:
    response = requests.get(MIMO_DATA_AGENT_TMP_ENDPOINT, params={
            'question': message,
            'test_token': mimo_test_token
        }
    )
    response = response.json() if response else None
    answer = response.get('answer', None) if response else None
    return answer