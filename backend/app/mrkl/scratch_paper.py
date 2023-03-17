from app.graph.db import GraphDB
from app.util.open_ai import OpenAIClient
from app.util.vectordb import Pinecone
from app.whitebox.chat_system import ChatSystem

system = ChatSystem(
    owner='test_user',
    graph_db=graph_db,
    vector_db=pinecone_client,
    openai_client=openai_client
)

print(system.run("What do they think about deadlines at Jefferies?"))
graph_db.close()