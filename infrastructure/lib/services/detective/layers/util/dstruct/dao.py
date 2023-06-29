import json
from datetime import datetime
from logging import getLogger
from typing import Any, Dict, List, Set

from dstruct.graphdb import Node, Relationship
from dstruct.model import (Block, Chunk, Entity, Property, StructuredProperty,
                           UnstructuredProperty)
from dstruct.vectordb import Row

_logger = getLogger('DStructDao')

class DStructDao:
    def __init__(self, library: str, log_level: int):
        self._library = library

        _logger.setLevel(log_level)

    def _properties_as_listed_dict(self, properties: Set[Property]) -> List[Dict[str, Any]]:
        dictionary_properties = []
        for property in properties:
            dictionary = {
                'key': property.key
            }
            if isinstance(property, StructuredProperty):
                dictionary['value'] = property.value
            elif isinstance(property, UnstructuredProperty):
                dictionary['chunks'] = [{
                    'order': chunk.order,
                    'text': chunk.text,
                } for chunk in property.chunks]
            else:
                raise ValueError(f'Unknown property type: {type(property)}')
            dictionary_properties.append(json.dumps(dictionary))
                
        return dictionary_properties
    
    def _listed_dict_as_properties(self, listed_dict: List[str]) -> Set[Property]:
        properties = set()
        for dictionary_property_str in listed_dict:
            try:
                dictionary_property = json.loads(dictionary_property_str)
                if dictionary_property.get('value'):
                    properties.add(StructuredProperty(
                    key=dictionary_property.get('key'),
                        value=dictionary_property.get('value'),
                    ))
                elif dictionary_property.get('chunks'):
                    properties.add(UnstructuredProperty(
                        key=dictionary_property.get('key'),
                        chunks=[Chunk(
                            order=chunk.get('order'),
                            text=chunk.get('text'),
                            embedding=None
                        ) for chunk in dictionary_property.get('chunks')],
                    ))
            except Exception as e:
                _logger.error(f'[_listed_dict_as_properties] failed to parse {dictionary_property_str} as JSON: {e}')
        return properties

    def block_to_node(self, block: Block, has_block_ids: Set[str] = None) -> Node:
        return Node(
            library=self._library,
            id=block.id,
            data={
                'label': block.label,
                'integration': block.integration,
                'connection': block.connection,
                'properties': self._properties_as_listed_dict(block.properties),
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
            integration=node.data.get('integration'),
            connection=node.data.get('connection'),
            properties=self._listed_dict_as_properties(node.data.get('properties')),
            last_updated_timestamp=node.data.get('last_updated_timestamp'),
            embedding=None
        )

    def entity_to_node(self, entity: Entity, mentioned_block_ids: Set[str] = None) -> Node:
        return Node(
            library=self._library,
            id=entity.name,
            data={
                'identifiables': list(entity.identifiables) if entity.identifiables else [],
            },
            relationships=[Relationship(
                library=self._library,
                id=block_id,
                type='Mentioned',
            ) for block_id in mentioned_block_ids] if mentioned_block_ids else []
        )

    def node_to_entity(self, node: Node) -> Entity:
        return Entity(
            name=node.id,
            identifiables=set(node.data.get('identifiables'))
        )

    def row_to_block(self, row: Row) -> Block:
        if row.type != 'block':
            raise ValueError('Row is not a block')

        return Block(
            id=row.id,
            label=row.label,
            integration=None,
            connection=None,
            properties=None,
            last_updated_timestamp=None,
            embedding=row.embedding
        )

    def row_to_chunk(self, row: Row) -> Chunk:
        if row.type != 'chunk':
            raise ValueError('Row is not a chunk')
        
        return Chunk(
            order=None,
            text=None,
            embedding=row.embedding
        )
    
    def _ts_to_date_day(self, timestamp: int) -> str:
        if not timestamp:
            return '1'
        return datetime.fromtimestamp(timestamp).strftime('%Y%m%d')
    
    def _date_day_to_ts(self, date_day: str) -> int:
        if date_day == '1':
            return None
        return int(datetime.strptime(date_day, '%Y%m%d').timestamp())

    def block_to_row(self, block: Block) -> Row:
        return Row(
            id=block.id,
            embedding=block.embedding,
            library=self._library,
            date_day=self._ts_to_date_day(block.last_updated_timestamp),
            type='block',
            label=block.label
        )