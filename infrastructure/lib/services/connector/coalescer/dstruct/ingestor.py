from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from dstruct.model import Block, Discovery, Metric, Stats
from dstruct.neo4j_ import Neo4j, Node
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
    blocks: List[Node]
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
    
    def _construct(self, discovery: Discovery) -> Ingest:
        succeeded = True
        pages: List[Node] = []
        blocks: List[Node] = []
        names: List[Node] = []
        rows: List[Row] = []
        error = None

        try:
            chunked_blocks = self._chunkify_blocks(discovery.blocks)
            if not discovery.is_valid():
                raise Exception('discovery is not valid')
            for chunked_block in chunked_blocks:
                last_updated_timestamp = max([block.last_updated_timestamp for block in chunked_block])
                date_day = datetime.fromtimestamp(last_updated_timestamp).strftime('%Y%m%d')
                block_id = ulid()
                
                blocks.append(Node(
                    library=self._library,
                    id=block_id,
                    properties={
                        'connection': self._connection,
                        'source': discovery.id,
                        'label': chunked_block[0].label,
                        'last_updated_timestamp': last_updated_timestamp,
                        'blocks': str([block.as_dict() for block in chunked_block]),
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