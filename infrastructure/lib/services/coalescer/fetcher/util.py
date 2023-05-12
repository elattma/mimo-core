from datetime import datetime
from typing import Generator, List

from model.blocks import Block, BlockStream, entity

MAX_BLOCK_SIZE = 600
MAX_BLOCK_OVERLAP = 50

def get_entity(self, id: str = None, name: str = None) -> entity:
    if not (id and name):
        return None
    return entity(id=id, value=name)

def get_timestamp_from_format(timestamp_str: str, format: str = None) -> int:
    if not (timestamp_str and format):
        return None
    timestamp_datetime = datetime.strptime(timestamp_str, format)
    return int(timestamp_datetime.timestamp())

def streamify_blocks(label: str, blocks: List[Block]) -> List[BlockStream]:
    if not blocks or len(blocks) < 1:
        return []
    final_blocks: List[BlockStream] = []
    temporary_blocks: List[Block] = []
    total_blocks_size = 0
    for block in blocks:
        if not block:
            continue
        block_size = len(str(block))
        if block_size < 1:
            continue

        if total_blocks_size + block_size >= MAX_BLOCK_SIZE:
            if len(temporary_blocks) > 0:
                final_blocks.append(BlockStream(label, temporary_blocks))
                while total_blocks_size > MAX_BLOCK_OVERLAP or (
                    total_blocks_size + block_size > MAX_BLOCK_SIZE
                    and total_blocks_size > 0
                ):
                    total_blocks_size -= len(str(temporary_blocks[0]))
                    temporary_blocks.pop(0)

        temporary_blocks.append(block)
        total_blocks_size += block_size
        
    if len(temporary_blocks) > 0:
        final_blocks.append(BlockStream(label, temporary_blocks))

    return final_blocks

def generate(label: str, blocks: List[Block]) -> Generator[BlockStream, None, None]:
    if not blocks or len(blocks) < 1:
        return
    for block in streamify_blocks(label, blocks):
        yield block