from dataclasses import dataclass
from datetime import datetime
from typing import List

from external.openai_ import OpenAI
from graph.blocks import BlockStream, SummaryBlock
from graph.neo4j_ import Block, Consists, Name, Neo4j, Page
from graph.pinecone_ import Pinecone, Row, RowType
from graph.translator import Translator
from ulid import ulid


@dataclass
class Ingest:
    block_streams: List[BlockStream]

MAX_TREE_BLOCKS_CHILDREN = 10

class Ingestor:
    def __init__(self, openai: OpenAI, neo4j: Neo4j, pinecone: Pinecone, library: str, connection: str):
        self._openai = openai
        self._neo4j = neo4j
        self._pinecone = pinecone
        self._library = library
        self._connection = connection
        self._translator = Translator()
    
    def blocks(self, blocks: List[BlockStream]) -> bool:
        pass

    def pages(self, pages: List[Page]) -> bool:
        pass

    def names(self, names: List[Name]) -> bool:
        pass

    def act(self, inputs: List[Ingest]) -> bool:
        succeeded = True
        pages: List[Page] = []
        rows: List[Row] = []
        for input in inputs:
            graph_blocks = self._get_graph_blocks(input.block_streams)
            page = Page(
                id=input.page_id,
                integration=input.integration,
                consists=[Consists(target=block) for block in graph_blocks],
            )
            pages.append(page)

            for block in graph_blocks:
                date_day = datetime.fromtimestamp(block.last_updated_timestamp).strftime('%Y%m%d')
                rows.append(Row(
                    id=block.id,
                    embedding=block.embedding,
                    library=input.library,
                    type=RowType.BLOCK,
                    date_day=date_day,
                    integration=input.integration,
                    connection=input.connection,
                    page_id=input.page_id,
                    block_label=block.label,
                ))
        
        try:
            self._neo4j.write(pages, input.library)
        except Exception as e:
            print('neo4j write failed:', str(e))
            succeeded = False

        try:
            self._pinecone.upsert(rows)
        except Exception as e:
            print('pinecone write failed:', str(e))
            succeeded = False

        return succeeded
    