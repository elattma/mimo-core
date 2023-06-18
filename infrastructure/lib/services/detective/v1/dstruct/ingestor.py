from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from dstruct.model import Block, Discovery, Metric, Stats
from dstruct.neo4j_ import Neo4j, Node
from dstruct.pinecone_ import Pinecone, Row
from ulid import ulid
from util.openai_ import OpenAI

MAX_TREE_BLOCKS_CHILDREN = 10
CHUNK_SIZE = 1000

@dataclass
class Ingest:
    discovery: Discovery
    page: Node
    rows: List[Row]

class Ingestor:
    discovery_queue: List[Discovery] = []

    def __init__(self, openai: OpenAI, neo4j: Neo4j, pinecone: Pinecone, library: str, connection: str, batch_size: int = 20):
        self._openai = openai
        self._neo4j = neo4j
        self._pinecone = pinecone
        self._library = library
        self._connection = connection
        self._batch_size = batch_size
        self._stats = Stats()

    def close(self):
        self.flush()
        self._neo4j.close()

    def _condense(self, discovery: Discovery) -> str:
        stringified_blocks = [str(block) for block in discovery.blocks]


        while len(stringified_blocks) > 1:
            stringified_blocks_len = len(stringified_blocks)
            temp_stringified_blocks = []
            for i in range(0, stringified_blocks_len, MAX_TREE_BLOCKS_CHILDREN):
                stringified_blocks_input = '\n\n'.join(stringified_blocks[i : min(i + MAX_TREE_BLOCKS_CHILDREN, stringified_blocks_len)])
                stringified_block = self._openai.summarize(stringified_blocks_input)
                temp_stringified_blocks.append(stringified_block)
            stringified_blocks = temp_stringified_blocks
        if len(stringified_blocks) != 1:
            raise Exception("_condense: len(stringified_blocks) != 1")
        return stringified_blocks[0]
    
    def _construct(self, discovery: Discovery) -> Ingest:
        try:
            if not discovery.is_valid():
                raise Exception('discovery is not valid')
            last_updated_timestamp = max([block._last_updated_timestamp for block in discovery.blocks])
            condensed = self._condense(discovery)
            page = Node(
                library=self._library,
                id=discovery.id,
                properties={
                    'connection': self._connection,
                    'type': discovery.type,
                    'condensed': condensed,
                    'blocks': str([block.as_dict() for block in discovery.blocks]),
                    'last_updated_timestamp': last_updated_timestamp,
                }
            )

            rows: List[Row] = []
            for block in discovery.blocks:
                block_embedding = self._openai.embed(str(block._properties))
                rows.append(Row(
                    id=block._id,
                    embedding=block_embedding,
                    library=self._library,
                    date_day=datetime.fromtimestamp(block._last_updated_timestamp).strftime('%Y%m%d') if block._last_updated_timestamp else None,
                    block_label=block._label,
                    page_type=discovery.type
                ))
            condensed_embedding = self._openai.embed(condensed)
            rows.append(Row(
                id=discovery.id,
                embedding=condensed_embedding,
                library=self._library,
                date_day=datetime.fromtimestamp(last_updated_timestamp).strftime('%Y%m%d') if last_updated_timestamp else None,
                block_label='condensed',
                page_type=discovery.type
            ))
            return Ingest(
                discovery=discovery,
                page=page,
                rows=rows
            )
        except Exception as e:
            print(f'[_construct] failed to construct {discovery.id}: {str(e)}')
            self._stats.tally(Metric.FAILED, 1)
            return None
    
    def flush(self) -> bool:
        print('[flush] flushing')
        if not self.discovery_queue:
            print('[flush] empty')
            return True
        self._stats.tally(Metric.FLUSHED, len(self.discovery_queue))
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            print('[flush] constructing', len(self.discovery_queue), 'ingests')
            futures = [executor.submit(self._construct, discovery) for discovery in self.discovery_queue]

        ingests: List[Ingest] = []
        for future in as_completed(futures):
            result: Ingest = future.result()
            if not result:
                continue
            ingests.append(result)

        try:
            block_ids = self._neo4j.get_source_ids(self._library, [ingest.discovery.id for ingest in ingests])
            self._neo4j.blocks([block for ingest in ingests for block in ingest.blocks])
            self._pinecone.upsert([rows for ingest in ingests for rows in ingest.rows])
            self._neo4j.delete(self._library, block_ids)
            self._pinecone.delete(block_ids)
        except Exception as e:
            print(f'failed to flush: {str(e)}')
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