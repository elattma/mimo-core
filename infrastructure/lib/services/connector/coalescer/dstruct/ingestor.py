from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from dstruct.model import Block, Discovery, Metric, Stats
from dstruct.neo4j_ import Neo4j, Node, Relationship
from dstruct.pinecone_ import Pinecone, Row
from ulid import ulid
from util.openai_ import OpenAI
from util.translator import Translator

MAX_TREE_BLOCKS_CHILDREN = 10
CHUNK_SIZE = 1000

@dataclass
class Ingest:
    succeeded: bool
    discovery: Discovery
    pages: List[Node]
    blocks: List[Node]
    names: List[Node]
    rows: List[Row]
    error: str

class Ingestor:
    discovery_queue: List[Discovery] = []

    def __init__(self, openai: OpenAI, translator: Translator, neo4j: Neo4j, pinecone: Pinecone, library: str, connection: str, batch_size: int = 20):
        self._openai = openai
        self._translator = translator
        self._neo4j = neo4j
        self._pinecone = pinecone
        self._library = library
        self._connection = connection
        self._batch_size = batch_size
        self._stats = Stats()

    def close(self):
        self.flush()
        self._neo4j.close()
    
    def _add_block(self, chunked_blocks: List[List[Block]], block: Block):
        if not chunked_blocks:
            chunked_blocks.append([])

        blocks_to_add: List[Block] = []
        for i in range(0, len(block.translated), CHUNK_SIZE):
            unstructured = block.unstructured[i : min(i + CHUNK_SIZE, len(block.translated))]
            if not unstructured:
                continue
            new_block = Block(
                label=block.label,
                last_updated_timestamp=block.last_updated_timestamp,
                properties=block.properties,
                unstructured=unstructured
            )

            new_block.translated = self._translator.translate([new_block])
            blocks_to_add.append(new_block)

        for block_to_add in blocks_to_add:
            chunked_block = chunked_blocks[-1]
            chunked_block_len = len(''.join([b.translated for b in chunked_block]))
            if chunked_block_len + len(block_to_add.translated) > CHUNK_SIZE and chunked_block_len > 0:
                chunked_blocks.append([])
                chunked_block = chunked_blocks[-1]
            chunked_block.append(block_to_add)

    def _chunkify_blocks(self, blocks: List[Block]) -> List[List[Block]]:
        for block in blocks:
            block.translated = self._translator.translate([block])

        chunked_blocks_dict: Dict[str, List[List[Block]]] = {}
        for block in blocks:
            if block.label not in chunked_blocks_dict:
                chunked_blocks_dict[block.label] = []
            self._add_block(chunked_blocks_dict[block.label], block)
        
        chunked_blocks: List[List[Block]] = []
        for grouped_chunked_blocks in chunked_blocks_dict.values():
            for blocks in grouped_chunked_blocks:
                for block in blocks:
                    if not block.is_valid():
                        raise Exception(f"block is not valid: {block}")
            chunked_blocks.extend(grouped_chunked_blocks)
        return chunked_blocks
    
    def _summarize(self, chunked_blocks: List[List[Block]]) -> str:        
        summaries = [block.translated for chunked_block in chunked_blocks for block in chunked_block]
        while len(summaries) > 1:
            summaries_len = len(summaries)
            temp_summaries = []
            for i in range(0, summaries_len, MAX_TREE_BLOCKS_CHILDREN):
                summary_input = '\n\n'.join(summaries[i : min(i + MAX_TREE_BLOCKS_CHILDREN, summaries_len)])
                summary = self._openai.summarize(summary_input)
                temp_summaries.append(summary)
            summaries = temp_summaries
        if len(summaries) != 1:
            raise Exception("_summarize: len(summaries) != 1")
        return summaries[0]
    
    def _construct(self, discovery: Discovery) -> Ingest:
        succeeded = True
        pages: List[Node] = []
        blocks: List[Node] = []
        names: List[Node] = []
        rows: List[Row] = []
        error = None

        page_lut = -1
        try:
            chunked_blocks = self._chunkify_blocks(discovery.blocks)
            discovery.summary = self._summarize(chunked_blocks)
            if not discovery.is_valid():
                raise Exception('discovery is not valid')
            for chunked_block in chunked_blocks:
                last_updated_timestamp = max([block.last_updated_timestamp for block in chunked_block])
                page_lut = max([page_lut, last_updated_timestamp])
                date_day = datetime.fromtimestamp(last_updated_timestamp).strftime('%Y%m%d')
                block_id = ulid()
                
                blocks.append(Node(
                    library=self._library,
                    id=block_id,
                    properties={
                        'label': chunked_block[0].label,
                        'last_updated_timestamp': last_updated_timestamp,
                        'blocks': str([block.as_dict() for block in chunked_block])
                    }
                ))
                
                embedding = self._openai.embed('\n\n'.join([block.translated for block in chunked_block]))
                rows.append(Row(
                    id=block_id,
                    embedding=embedding,
                    library=self._library,
                    date_day=date_day,
                    block_label=chunked_block[0].label,
                    page_type=discovery.type
                ))
            pages = [Node(
                library=self._library,
                id=discovery.id,
                properties={
                    'connection': self._connection,
                    'type': discovery.type,
                    'last_updated_timestamp': page_lut,
                    'summary': discovery.summary
                },
                relationships=[Relationship(
                    library=self._library,
                    id=block.id
                ) for block in blocks]
            )]
            embedding = self._openai.embed(discovery.summary)
            rows.append(Row(
                id=discovery.id,
                embedding=embedding,
                library=self._library,
                date_day=datetime.fromtimestamp(page_lut).strftime('%Y%m%d'),
                block_label='mimo#summary',
                page_type=discovery.type
            ))
            for entity in discovery.entities:
                names.append(Node(
                    library=self._library,
                    id=entity.id,
                    properties={
                        'value': entity.value,
                        'roles': entity.roles,
                    },
                    relationships=[Relationship(
                        library=self._library,
                        id=discovery.id
                    )]
                ))
        except Exception as e:
            succeeded = False
            error = str(e)
            print(f'failed to ingest {discovery.id}: {str(e)}')
        return Ingest(
            succeeded=succeeded, 
            discovery=discovery,
            pages=pages,
            blocks=blocks,
            names=names,
            rows=rows,
            error=error
        )
    
    def _cleanup(self):
        try:
            deleted_blocks = self._neo4j.cleanup(self._library)
            print(deleted_blocks)
            self._pinecone.delete(deleted_blocks, self._library)
        except Exception as e:
            print(f'failed to cleanup: {str(e)}')
    
    def flush(self) -> bool:
        print('flushing!')
        if not self.discovery_queue:
            return True
        self._stats.tally(Metric.FLUSHED, len(self.discovery_queue))
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self._construct, discovery) for discovery in self.discovery_queue]

        ingests: List[Ingest] = []
        for future in as_completed(futures):
            result: Ingest = future.result()
            ingests.append(result)

        try:
            self._neo4j.blocks([block for ingest in ingests for block in ingest.blocks])
            self._neo4j.pages([page for ingest in ingests for page in ingest.pages])
            self._neo4j.names([name for ingest in ingests for name in ingest.names])
            self._pinecone.upsert([rows for ingest in ingests for rows in ingest.rows])
            self._cleanup()
        except Exception as e:
            print(f'failed to flush: {str(e)}')
            # TODO: undo changes? at the very least remove blocks, pages, names, and upserted
            self._stats.tally(Metric.FAILED, len(self.discovery_queue))
            return False
        
        # TODO: get the exact # from each of the operations
        self._stats.tally(Metric.SUCCEEDED, len(self.discovery_queue))
        self.discovery_queue = []
        return True

    def add(self, discovery: Discovery) -> bool:
        self._stats.tally(Metric.TOTAL, 1)
        self.discovery_queue.append(discovery)
        if len(self.discovery_queue) >= self._batch_size:
            return self.flush()
        return True