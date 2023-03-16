import os

from mrkl_agent import MRKLAgent
from open_ai import OpenAIChat, OpenAIText
from prompt import (ChatPrompt, ChatPromptMessage, ChatPromptMessageRole,
                    TextPrompt)
from tool import Tool, Toolkit

MAX_STEPS = 2

os.environ["OPENAI_API_KEY"] = ""

text_llm = OpenAIText()
chat_llm = OpenAIChat()

def get_advice_chat(s: str) -> str:
    system_message = ChatPromptMessage(
        role=ChatPromptMessageRole.SYSTEM.value,
        content=(
          "You are a helpful assistant whose job is to give life advice.\n"
          "You should always begin your responses with 'I am here to advise!'"
        )
    )
    user_message = ChatPromptMessage(
        role=ChatPromptMessageRole.USER.value,
        content=s
    )
    prompt = ChatPrompt([system_message, user_message])
    return chat_llm.predict(prompt)

def get_advice_text(s: str) -> str:
    prompt = TextPrompt((
        "You are a helpful assistant whose job is to give life advice.\n"
        "You should always begin your responses with \"I am here to advise!\""
        f"{s}"
    ))
    return text_llm.predict(prompt)


def get_motivation_chat(s: str) -> str:
    system_message = ChatPromptMessage(
        role=ChatPromptMessageRole.SYSTEM.value,
        content=(
          "You are a motivating assistant whose job is to give encouragement.\n"
          "You should always begin your responses with 'I am here to motivate!'"
        )
    )
    user_message = ChatPromptMessage(
        role=ChatPromptMessageRole.USER.value,
        content=s
    )
    prompt = ChatPrompt([system_message, user_message])
    return chat_llm.predict(prompt)

def get_motivation_text(s: str) -> str:
    prompt = TextPrompt((
        "You are a helpful assistant whose job is to give encouragement.\n"
        "You should always begin your responses with \"I am here to motivate!\""
        f"{s}"
    ))
    return text_llm.predict(prompt)

toolkit = Toolkit([
    Tool(
      name="Advice",
      description=(
        "Used when advice is needed. "
        "Input should be a request for advice. "
        "Output will be the answer."
      ),
      func=get_advice_chat
    ),
    Tool(
      name="Motivation",
      description=(
        "Used when motivation is needed. "
        "Input should be a request for motivation. "
        "Output will be text."
      ),
      func=get_motivation_chat
    ),
])

prefix = (
    "You are a helpful assistant whose job is to respond to an input to the "
    "best of your ability using the tools that you have access to.\n"
    "You have access to the following tools:"
)
suffix = (
    "Remember that you should address each part of the original input in "
    "your final answer.\n"
    "Begin!"
)

prompt_template = MRKLAgent.create_text_prompt_template(
    toolkit,
    prefix=prefix,
    suffix=suffix
)

agent = MRKLAgent(
    llm=text_llm,
    toolkit=toolkit,
    prompt_template=prompt_template,
    max_steps=MAX_STEPS
)

agent.run("How do I improve my grades? And, how do I stop feeling lazy always?")