from typing import Dict, List

from graph.model import BlockFilter, GraphFilter, NameFilter
from mystery.context_basket.model import Block, Context
from neo4j import GraphDatabase


class Neo4j:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        with self.driver:
            self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def get_raw_context(self, filter: GraphFilter) -> List[Context]:
        with self.driver.session() as session:
            result = session.execute_read(self._get_raw_context, filter)
            return result
    
    @staticmethod
    def _with_block_filter(filter: BlockFilter, query_wheres: List[str], params: Dict):
        query_wheres.append('block.library = $library')
        if filter.id:
            query_wheres.append(f'block.id IN $block_ids')
            params['block_ids'] = list(filter.id)
        if filter.connection:
            query_wheres.append(f'block.connection IN $block_connections')
            params['block_connections'] = list(filter.connection)
        if filter.source:
            query_wheres.append(f'block.source IN $block_sources')
            params['block_sources'] = list(filter.source)
        if filter.label:
            query_wheres.append(f'block.label IN $block_labels')
            params['block_labels'] = list(filter.label)
        if filter.time_range:
            query_wheres.append(f'(block.timestamp >= $block_start_timestamp AND block.timestamp <= $block_end_timestamp)')
            params['block_start_timestamp'] = filter.time_range[0]
            params['block_end_timestamp'] = filter.time_range[1]
        if filter.kv_match:
            for kv_match in filter.kv_match:
                query_wheres.append(f'block.{kv_match.key} = {kv_match.value}')
        if filter.key_regex_match:
            for key_regex_match in filter.key_regex_match:
                query_wheres.append(f'block.{key_regex_match.key} =~ $key_regex_match')
                params['key_regex_match'] = key_regex_match.match

    @staticmethod
    def _with_name_filter(filter: NameFilter, query_wheres: List[str], params: Dict):
        query_wheres.append('name.library = $library')
        if filter.id:
            query_wheres.append(f'name.id IN $name_ids')
            params['name_ids'] = list(filter.id)
        if filter.value:
            query_wheres.append(f'name.value IN $name_values')
            params['name_values'] = list(filter.value)

    @staticmethod
    def _to_context(record: Dict) -> Context:
        source = record.get('source')
        connection = record.get('connection')
        node_blocks: List[Dict] = record['blocks']
        blocks = []
        for node_block in node_blocks:
            blocks = node_block.get('blocks')
            blocks: List[Dict] = blocks if blocks else []
            blocks.append(Block(
                id=node_block.get('id'),
                label=node_block.get('label'),
                last_updated_timestamp=node_block.get('last_updated_timestamp'),  
                blocks=blocks,
            ))
        return Context(
            connection=connection,
            source=source,
            blocks=blocks
        )

    @staticmethod
    def _get_raw_context(tx, filter: GraphFilter) -> List[Context]:
        if not (filter and filter.library):
            return None
        
        params = {
            'library': filter.library
        }
        query_wheres = []
        if filter.block_filter:
            Neo4j._with_block_filter(filter.block_filter, query_wheres, params)
        
        # TODO: implement views
        # TODO: optimize entity lookups with names
        if filter.name_filter:
            Neo4j._with_name_filter(filter.name_filter, query_wheres, params)
        
        order = ''
        if filter.order and filter.order.property and filter.order.direction:
            order = f'ORDER BY {filter.order.property} {filter.order.direction}'

        pagination = ''
        if filter.pagination:
            if filter.pagination.offset:
                pagination += f'SKIP {filter.pagination.offset}'
            pagination += f'LIMIT {filter.pagination.count if filter.pagination.count else 50}'

        query_where = ' AND '.join(query_wheres)
        query = (
            f'MATCH (block:Block) '
            f'WHERE {query_where} '
            'WITH block.source AS source, block.connection AS connection, COLLECT(block) AS block_nodes '
            'RETURN source, connection, block_nodes '
            f'{order} '
            f'{pagination}'
        )
        print(f'[Neo4j]: Executing query... {query}')
        result = tx.run(query, **params)
        records = list(result)

        print('[Neo4j]: Query completed!')
        print('[Neo4j]: Sample:', records[0] if records else 'empty!')

        return [Neo4j._to_context(record) for record in records]
    