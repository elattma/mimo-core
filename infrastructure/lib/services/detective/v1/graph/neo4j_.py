import json
from typing import Dict, List

from graph.model import GraphFilter
from mystery.context_basket.model import Context, Source
from neo4j import GraphDatabase, Record


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
    def _parse_context(record: Record) -> Context:
        if not record:
            return None
        
        page = record.get('page', None)
        page_id = page.get('id', None) if page else None
        connection = page.get('connection', None) if page else None

        node_blocks = record.get('blocks', None)
        label = node_blocks.get('label', None) if node_blocks else None
        last_updated_timestamp = node_blocks.get('last_updated_timestamp', None) if node_blocks else None
        blocks: str = node_blocks.get('blocks', None) if node_blocks else None
        blocks: List[Dict] = json.loads(blocks) if blocks else None

        return Context(
            source=Source(
                page_id=page_id,
                connection=connection
            ),
            label=label,
            last_updated_timestamp=last_updated_timestamp,
            blocks=blocks
        )

    @staticmethod
    def _get_raw_context(tx, filter: GraphFilter) -> List[Context]:
        # TODO: refactor to make this more readable
        # TODO: can get relationships for pages if needed to determine which can be joined.
        # or what views the user has over their data
        if not (filter and filter.library):
            return None
        
        params = {
            'library': filter.library
        }
        query_wheres = ['block.library = $library', 'page.library = $library', 'name.library = $library']
        if filter.page_filter:
            page_filter = filter.page_filter
            if page_filter.id:
                query_wheres.append(f'page.id IN $page_ids')
                params['page_ids'] = list(page_filter.id)
            if page_filter.connection:
                query_wheres.append(f'page.connection IN $page_connections')
                params['page_connections'] = list(page_filter.connection)
            if page_filter.type:
                query_wheres.append(f'page.type IN $page_types')
                params['page_types'] = list(page_filter.type)
            if page_filter.time_range:
                query_wheres.append(f'(page.timestamp >= $page_start_timestamp AND page.timestamp <= $page_end_timestamp)')
                params['page_start_timestamp'] = page_filter.time_range[0]
                params['page_end_timestamp'] = page_filter.time_range[1]

        if filter.block_filter:
            block_filter = filter.block_filter
            if block_filter.id:
                query_wheres.append(f'block.id IN $block_ids')
                params['block_ids'] = list(block_filter.id)
            if block_filter.label:
                query_wheres.append(f'block.label IN $block_labels')
                params['block_labels'] = list(block_filter.label)
            if block_filter.time_range:
                query_wheres.append(f'(block.timestamp >= $block_start_timestamp AND block.timestamp <= $block_end_timestamp)')
                params['block_start_timestamp'] = block_filter.time_range[0]
                params['block_end_timestamp'] = block_filter.time_range[1]
            if block_filter.kv_match:
                for kv_match in block_filter.kv_match:
                    query_wheres.append(f'block.{kv_match.key} = {kv_match.value}')
            if block_filter.key_regex_match:
                for key_regex_match in block_filter.key_regex_match:
                    query_wheres.append(f'block.{key_regex_match.key} =~ $key_regex_match')
                    params['key_regex_match'] = key_regex_match.match

        if filter.name_filter:
            name_filter = filter.name_filter
            if name_filter.id:
                query_wheres.append(f'name.id IN $name_ids')
                params['name_ids'] = list(name_filter.id)
            if name_filter.value:
                query_wheres.append(f'name.value IN $name_values')
                params['name_values'] = list(name_filter.value)
            # TODO: filter the relationship on roles
        
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
            f'MATCH (name:Name)-[:Mentions]->(page:Page)-[:Consists]->(block:Block) '
            f'WHERE {query_where} '
            f'WITH page, COLLECT(block) as blocks, max(block.last_updated_timestamp) AS order_by, count(name) AS name_count '
            'RETURN page, blocks '
            f'{order} '
            f'{pagination}'
        )
        print(f'[Neo4j]: Executing query... {query}')
        result = tx.run(query, **params)
        records = list(result)

        print('[Neo4j]: Query completed!')
        print('[Neo4j]: Sample:', records[0] if records else 'empty!')
        return [Neo4j._parse_context(record) for record in records] if records else None
    