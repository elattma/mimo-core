from datetime import datetime
from typing import List, Set

from dstruct.graphdb import Node, Relationship
from dstruct.model import Block, Chunk, Entity
from dstruct.vectordb import Row


class DStructDao:
    def __init__(self, library: str):
        self._library = library

    def block_to_node(self, block: Block, has_block_ids: Set[str] = None) -> Node:
        return Node(
            library=self._library,
            id=block.id,
            data={
                'label': block.label,
                'properties': str(list(block.properties)),
                'last_updated_timestamp': block.last_updated_timestamp,
            },
            relationships=[Relationship(
                library=self._library,
                id=block_id,
                type='Has',
            ) for block_id in has_block_ids] if has_block_ids else []
        )

    def node_to_block(self, node: Node) -> Block:
        return Block(
            id=node.id,
            label=node.data.get('label'),
            properties=set(node.data.get('properties')),
            last_updated_timestamp=node.data.get('last_updated_timestamp'),
            embedding=None
        )

    def entity_to_node(self, entity: Entity, mentioned_block_ids: Set[str] = None) -> Node:
        return Node(
            library=self._library,
            id=entity.id,
            data={
                'value': entity.value,
                'identifiables': str(list(entity.identifiables)),
            },
            relationships=[Relationship(
                library=self._library,
                id=block_id,
                type='Mentioned',
            ) for block_id in mentioned_block_ids] if mentioned_block_ids else []
        )

    def node_to_entity(self, node: Node) -> Entity:
        return Entity(
            id=node.id,
            identifiables=set(node.data.get('identifiables')),
            value=node.data.get('value'),
        )

    def row_to_block(self, row: Row) -> Block:
        if row.type != 'block':
            raise ValueError('Row is not a block')

        return Block(
            id=row.id,
            label=row.label,
            properties=None,
            last_updated_timestamp=None,
            embedding=row.embedding
        )

    def row_to_chunk(self, row: Row) -> Chunk:
        if row.type != 'chunk':
            raise ValueError('Row is not a chunk')
        
        return Chunk(
            ref_id=row.id,
            order=None,
            text=None,
            embedding=row.embedding
        )

    def block_to_row(self, block: Block) -> Row:
        return Row(
            id=block.id,
            embedding=block.embedding,
            library=self._library,
            date_day=datetime.fromtimestamp(block.last_updated_timestamp).strftime('%Y%m%d') if block.last_updated_timestamp else None,
            type='block',
            label=block.label
        )

    def block_chunks_to_rows(self, block: Block) -> List[Row]:
        rows = []
        date_day = datetime.fromtimestamp(block.last_updated_timestamp).strftime('%Y%m%d') if block.last_updated_timestamp else None
        for unstructured in block.get_unstructured_properties():
            rows.extend([Row(
                id=chunk.ref_id,
                embedding=chunk.embedding,
                library=self._library,
                date_day=date_day,
                type='chunk',
                label=block.label
            ) for chunk in unstructured.chunks])

        return rows