import os
import re
from typing import List

from mrkl_agent import MRKLAgent
from openaillm import OpenAILLM
from tool import Tool, Toolkit

os.environ["OPENAI_API_KEY"] = (
    "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"
)


def parser(s: str) -> List[int]:
    return list(map(lambda x: int(x), re.split(r"\+|-|/|\*", s)))


def add(nums: List[int]) -> str:
    return str(nums[0] + nums[1])


def subtract(nums: List[int]) -> str:
    return str(nums[0] - nums[1])


def multiply(nums: List[int]) -> str:
    return str(nums[0] * nums[1])


def divide(nums: List[int]) -> str:
    return str(nums[0] // nums[1])


calculator_toolkit = Toolkit(
    [
        Tool(
            name="Add",
            description=(
                "Adds two numbers together. "
                "Input should be a mathematical expression of the form a+b. "
                "Output will be a number."),
            func=add,
            parser=parser
        ),
        Tool(
            name="Subtract",
            description=(
                "Subtracts one number from another. "
                "Input should be a mathematical expression of the form a-b. "
                "Output will be a number."

            ),
            func=subtract,
            parser=parser
        ),
        Tool(
            name="Multiply",
            description=(
                "Multiplies two numbers. "
                "Input should be a mathematical expression of the form a*b. "
                "Output will be a number."
            ),
            func=multiply,
            parser=parser
        ),
        Tool(
            name="Divide",
            description=(
                "Divides one number by another. "
                "Input should be a mathematical expression of the form a/b. "
                "Output will be a number."
            ),
            func=divide,
            parser=parser
        ),
    ]
)

llm = OpenAILLM()

calculator_prompt_template = MRKLAgent.create_prompt_template(
    calculator_toolkit)

calculator_agent = MRKLAgent(
    llm,
    calculator_toolkit,
    prompt_template=calculator_prompt_template
)


def answer_question(question: str) -> str:
    return llm.predict(question)


general_knowledge_toolkit = Toolkit([
    Tool(
        name="Answer",
        description=("Answers general knowledge questions. "
                     "Input should be a question. "
                     "Output will be the answer to the question."),
        func=answer_question
    )
])

general_knowledge_prompt_template = MRKLAgent.create_prompt_template(
    general_knowledge_toolkit
)

general_knowledge_agent = MRKLAgent(
    llm,
    general_knowledge_toolkit,
    prompt_template=general_knowledge_prompt_template
)

orchestrator_toolkit = Toolkit([
    Tool(
        name="Calculator",
        description=("Evaluates mathematical expressions. "
                     "Input should be a mathematical expression. "
                     "Output will be the result of evaluation the expression"),
        func=calculator_agent.run
    ),
    Tool(
        name="General Knowledge",
        description=("Finds the answer to questions about general knowledge. "
                     "Input should be the question and the context needed to "
                     "answer it. Output will be the answer to the question."),
        func=general_knowledge_agent.run
    )
])

orchestrator_prompt_template = MRKLAgent.create_prompt_template(
    orchestrator_toolkit
)

orchestrator_agent = MRKLAgent(
    llm,
    orchestrator_toolkit,
    prompt_template=orchestrator_prompt_template
)

print(orchestrator_agent.run((
    "How many Olympic gold medals did Michael Phelps win? "
    "Also, who played Han Solo in the Star Wars movies? What is the sum of "
    "Phelp's gold medal tally and the number of original Star Wars movies? "
    "Make sure your final answer addresses each of my questions fully."
)))
