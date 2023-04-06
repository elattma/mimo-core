from dataclasses import dataclass
from datetime import datetime
from typing import List

from graph.blocks import BlockStream, SummaryBlock
from graph.neo4j_ import Block, Consists, Document, Mentioned, Name, Neo4j
from graph.pinecone_ import Pinecone, Row, RowType
from layers.external.openai_ import OpenAI
from mystery.namer import Namer
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
    block_streams: List[BlockStream]
    timestamp: int

@dataclass
class IngestResponse:
    succeeded: bool
    integration: str

MAX_TREE_BLOCKS_CHILDREN = 10

class Ingestor:
    def __init__(self, openai: OpenAI, neo4j: Neo4j, pinecone: Pinecone):
        self._openai = openai
        self._neo4j = neo4j
        self._pinecone = pinecone
        self._namer = Namer(openai)

    def _get_block_names(self, block_streams: List[BlockStream]) -> List[Name]:
        names = set()
        for block_stream in block_streams:
            block_stream_names = self._namer.get_block_names(block_stream)
            if not block_stream_names:
                continue
        
            for name in block_stream_names:
                names.add(name)
        return list(names)

    def _get_graph_blocks(self, block_streams: List[BlockStream]) -> List[Block]:
        if not (block_streams and len(block_streams) > 0):
            return []

        # TODO: need to handle dynamic tree children in case where the blocks dont fit
        stringified_blocks = [str(block_stream) for block_stream in block_streams]

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
        summary_last_updated_timestamp = 0
        
        for block_stream in block_streams:
            block_str = str(block_stream)
            block_embedding = self._openai.embed(block_str)
            last_updated_timestamp = max([block.last_updated_timestamp for block in block_stream.blocks])
            summary_last_updated_timestamp = max(summary_last_updated_timestamp, last_updated_timestamp)
            graph_block = Block(
                id=ulid(), 
                embedding=block_embedding, 
                label=block_stream.label, 
                content=block_str,
                last_updated_timestamp=last_updated_timestamp
            )
            graph_blocks.append(graph_block)

        block_embedding = self._openai.embed(stringified_blocks[0])
        summary_block = Block(
            id=ulid(), 
            embedding=block_embedding, 
            label=SummaryBlock._LABEL, 
            content=stringified_blocks[0],
            last_updated_timestamp=summary_last_updated_timestamp
        )
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
        succeeded = True
        try:
            names = self._get_block_names(input.block_streams)
            graph_blocks = self._get_graph_blocks(input.block_streams)
            document = self._get_document(
                document_id=input.document_id,
                integration=input.integration,
                blocks=graph_blocks
            )
            name_mentioned = [Mentioned(document)]
            for name in names:
                name.mentioned = name_mentioned
            pinecone_response = self._pinecone_write(owner=input.owner, document=document)
            neo4j_response = self._neo4j_write(owner=input.owner, documents=[document], names=names, timestamp=input.timestamp)

            print(pinecone_response)
            print(neo4j_response)
        except Exception as e:
            print(e)
            succeeded = False

        return IngestResponse(
            succeeded=succeeded,
            integration=input.integration,
        )

    def _pinecone_write(self, owner: str, document: Document) -> bool:
        rows: List[Row] = []
        for block in document.consists:
            date_day = datetime.fromtimestamp(block.target.last_updated_timestamp).strftime('%Y%m%d')
            block_row = Row(
                id=block.target.id,
                embedding=block.target.embedding,
                owner=owner,
                type=RowType.BLOCK,
                date_day=int(date_day),
                integration=document.integration,
                document_id=document.id,
                block_label=block.target.label,
            )
            rows.append(block_row)

        return self._pinecone.upsert(rows)

    def _neo4j_write(self, documents: List[Document], names: List[Name], owner: str, timestamp: int) -> bool:
        return self._neo4j.write(documents=documents, names=names, owner=owner, timestamp=timestamp)