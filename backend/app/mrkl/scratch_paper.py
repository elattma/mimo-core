import os
from typing import Optional, Union

from app.graph.blocks import ChunkFilter, ProperNounFilter
from mrkl_agent import MRKLAgent
from openaillm import OpenAILLM
from tool import Tool, Toolkit

from backend.app.graph.blocks import QueryFilter
from backend.app.graph.db import GraphDB

os.environ["OPENAI_API_KEY"] = (
    "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"
)

llm = OpenAILLM(temperature=0)


def fetch_chunks(
        chunk_filter: ChunkFilter = None,
        propernoun_filter: ProperNounFilter = None
) -> str:
    user = None
    document_filter = None
    graph_db: GraphDB = None
    graph_db.get_chunks(query_filter=QueryFilter(
        user=user,
        document_filter=document_filter,
        chunk_filter=chunk_filter,
        propernoun_filter=propernoun_filter
    ))
    pass


fetch_chunks_tool = Tool(
    name="Fetch Chunks",
    description=(
        "Used to fetch information as chunks of text  "
    )
)

orchestration_toolkit = Toolkit([
    Tool(
        name="Fetch Context",
        description=(
            "Used to fetch any company data needed to properly answer a question. "
            "Input should be a description of the needed data. "
            "Output will be that data. "
        ),
        func=data_layer_agent.run,
    ),
    Tool(
        name="Task Execution",
        description=(
            "Used to produce the final answer to the question. "
            "Input should be the question, the memory, and additional context. "
            "Output will be the answer to the question. "
        ),
        func=executor_agent.run
    )
])

orchestrator_prompt_template = MRKLAgent.create_prompt_template(
    orchestration_toolkit
)

orchestrator_agent = MRKLAgent(
    llm=llm,
    toolkit=orchestration_toolkit,
    prompt_template=orchestrator_prompt_template,
)

print(orchestrator_agent.run("Respond to my most recent email from Alex."))
