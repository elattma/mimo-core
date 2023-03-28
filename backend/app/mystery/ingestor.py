from dataclasses import dataclass
from datetime import datetime
from typing import List

from app.client._neo4j import Block, Consists, Document, Neo4j
from app.client._openai import OpenAI
from app.client._pinecone import Pinecone, Row, RowType
from app.model.blocks import BlockStream, SummaryBlock
from ulid import ulid


@dataclass
class Triplet:
    subject: str
    predicate: str
    object: str

@dataclass
class IngestInput:
    owner: str
    integration: str
    document_id: str
    blocks: List[BlockStream]
    timestamp: int

@dataclass
class IngestResponse:
    succeeded: bool
    integration: str
    timestamp: int


MAX_TREE_BLOCKS_CHILDREN = 10


class Ingestor:
    def __init__(self, openai: OpenAI, neo4j: Neo4j, pinecone: Pinecone):
        self._openai = openai
        self._neo4j = neo4j
        self._pinecone = pinecone

    def _get_graph_blocks(self, block_streams: List[BlockStream]) -> List[Block]:
        if not (block_streams and len(block_streams) > 0):
            return []

        # TODO: need to handle dynamic tree children in case where the blocks dont fit
        stringified_blocks = [block_stream.to_str() for block_stream in block_streams]
        while len(stringified_blocks) > 1:
            stringified_blocks_len = len(stringified_blocks)
            temp_stringified_blocks = []
            for i in range(0, stringified_blocks_len, MAX_TREE_BLOCKS_CHILDREN):
                summary = self._openai.summarize(
                    "\n\n".join(
                        stringified_blocks[
                            i : min(i + MAX_TREE_BLOCKS_CHILDREN, stringified_blocks_len)
                        ]
                    )
                )
                temp_stringified_blocks.append(summary)
            stringified_blocks = temp_stringified_blocks
        if len(stringified_blocks) != 1:
            raise Exception("_get_graph_blocks: len(stringified_blocks) != 1")

        graph_blocks: List[Block] = []
        for block_stream in block_streams:
            block_str = block_stream.to_str()
            block_embedding = self._openai.embed(block_str)
            print(block_stream.label)
            graph_block = Block(id=ulid(), embedding=block_embedding, label=block_stream.label, content=block_str)
            graph_blocks.append(graph_block)
        
        block_embedding = self._openai.embed(stringified_blocks[0])
        summary_block = Block(id=ulid(), embedding=block_embedding, label=SummaryBlock._LABEL, content=stringified_blocks[0])
        graph_blocks.append(summary_block)
        return graph_blocks

    def _get_document(
        self, document_id: str, integration: str, blocks: List[Block]
    ) -> Document:
        document = Document(
            id=document_id,
            integration=integration,
            consists=[Consists(target=block) for block in blocks],
        )
        return document

    def ingest(self, input: IngestInput) -> IngestResponse:
        date_day = datetime.utcfromtimestamp(input.timestamp).strftime('%Y%m%d')

        succeeded = True
        try:
            graph_blocks = self._get_graph_blocks(input.blocks)
            document = self._get_document(
                document_id=input.document_id,
                integration=input.integration,
                blocks=graph_blocks
            )
            pinecone_response = self._pinecone_write(owner=input.owner, document=document, date_day=date_day)
            neo4j_response = self._neo4j_write(owner=input.owner, documents=[document], timestamp=input.timestamp)

            print(pinecone_response)
            print(neo4j_response)
        except Exception as e:
            print(e)
            succeeded = False

        return IngestResponse(
            succeeded=succeeded,
            integration=input.integration,
            timestamp=input.timestamp,
        )

    def _pinecone_write(self, owner: str, document: Document, date_day: int) -> bool:
        rows: List[Row] = []
        for block in document.consists:
            block_row = Row(
                id=block.target.id,
                embedding=block.target.embedding,
                owner=owner,
                integration=document.integration,
                document_id=document.id,
                type=RowType.BLOCK,
                date_day=date_day,
            )
            rows.append(block_row)

        return self._pinecone.upsert(rows)

    def _neo4j_write(self, documents: List[Document], owner: str, timestamp: int) -> bool:
        return self._neo4j.create_document_blocks(
            documents=documents, owner=owner, timestamp=timestamp
        )