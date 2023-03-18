from app.graph.db import GraphDB
from app.util.open_ai import OpenAIClient
from app.util.vectordb import Pinecone
from app.whitebox.context_agent import ContextAgent
from app.whitebox.system import ChatSystem

pinecone_client = Pinecone(
    api_key='', environment='')
graph_db = GraphDB(uri='',
                   user='', password='')
openai_client = OpenAIClient(
    api_key='')

chat_system = ChatSystem(
    owner='test_user',
    graph_db=graph_db,
    vector_db=pinecone_client,
    openai_client=openai_client
)

print(chat_system.run((
    'Write the javascript code for a clickable button'
)))

graph_db.close()
