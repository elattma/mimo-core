import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Literal, Set

from blocks import PageType
from neo4j import GraphDatabase, Record

UNIQUE_PATTERN_MIMO_PLACEHOLDER = '<UNQIUE_PLACEHOLDER>'


@dataclass
class Node(ABC):
    library: str
    id: str
    timestamp: int = None

    @staticmethod
    @abstractmethod
    def get_index_properties():
        return ['timestamp']

    @staticmethod
    def get_index_keys():
        return ['library', 'id']
    
    def __hash__(self):
        return hash((self.library, self.id))
    
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.library == other.library and self.id == other.id

    def get_neo4j_properties(self):
        return {
            'library': self.library,
            'id': self.id,
            'timestamp': self.timestamp,
        }


@dataclass
class Block(Node):
    embedding: List[float]
    label: str
    content: str

    @staticmethod
    def get_index_properties():
        return super().get_index_properties() + ['label', 'content']

    def get_neo4j_properties(self):
        map = super().get_neo4j_properties()
        map['label'] = self.label
        map['content'] = self.content
        return map


@dataclass
class Consists:
    target: Node


@dataclass
class Page(Node):
    type: PageType
    connection: str
    summary: str
    consists: List[Consists]

    @staticmethod
    def get_index_properties():
        return super().get_index_properties() + ['type', 'connection', 'summary']

    def get_neo4j_properties(self):
        map = super().get_neo4j_properties()
        map['type'] = self.type.value
        map['connection'] = self.connection
        map['summary'] = self.summary
        map['consists'] = [consist.target.get_neo4j_properties() for consist in self.consists]
        return map


@dataclass
class Mentioned:
    target: Node


@dataclass
class Name(Node):
    value: str
    mentioned: List[Mentioned]

    @staticmethod
    def get_index_properties():
        return super().get_index_properties() + ['value']

    def get_neo4j_properties(self):
        map = super().get_neo4j_properties()
        map['value'] = self.value
        map['mentioned'] = [mention.target.get_neo4j_properties() for mention in self.mentioned]
        return map


@dataclass
class PageFilter:
    ids: Set[str] = None
    integrations: Set[str] = None
    time_range: tuple[int, int] = None


@dataclass
class ContentItem:
    key: str
    value: str


@dataclass
class Matcher:
    match: str
    filter: str = None


@dataclass
class ContentMatch:
    match: str
    label: str = None
    filter: str = None

    @staticmethod
    def from_dict(matcher_dict: dict, label: str = None, filter: str = None):
        ContentMatch.replace_null_fields(matcher_dict)
        match = json.dumps(matcher_dict).replace(
            f'"{ContentMatch.get_any_match_placeholder()}"', '"([^"]*)"'
        )
        return ContentMatch(match=f'.*{match}.*', label=label, filter=filter)

    @staticmethod
    def from_contains(substring: str):
        return ContentMatch(match=f'.*{substring}.*')

    @staticmethod
    def get_entity_id_match_placeholder():
        return '<ENTITY_ID_MATCH_PLACEHOLDER>'

    @staticmethod
    def get_any_match_placeholder():
        return '<ANY_MATCH_PLACEHOLDER>'

    @staticmethod
    def replace_null_fields(dictionary: dict):
        for key, value in dictionary.items():
            if not value:
                dictionary[key] = ContentMatch.get_any_match_placeholder()
            elif isinstance(value, dict):
                ContentMatch.replace_null_fields(value)

    def __hash__(self):
        return hash((self.label))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.label == other.label


@dataclass
class BlockFilter:
    ids: Set[str] = None
    labels: Set[str] = None
    content_items: List[ContentItem] = None
    time_range: tuple[int, int] = None
    regex_matches: Set[ContentMatch] = None


@dataclass
class NameFilter:
    ids: Set[str] = None
    names: Set[str] = None


class OrderDirection(Enum):
    ASC = 'ASC'
    DESC = 'DESC'


@dataclass
class OrderBy:
    direction: OrderDirection
    node: Literal['page', 'block', 'name']
    property: Literal['last_updated_timestamp', 'id']


@dataclass
class Limit:
    offset: int
    count: int


@dataclass
class QueryFilter:
    library: str
    page_filter: PageFilter = None
    block_filter: BlockFilter = None
    name_filter: NameFilter = None
    order_by: OrderBy = None
    limit: Limit = None


class Neo4j:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        with self.driver:
            self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def blocks(self, blocks: List[Block]):
        with self.driver.session(database='neo4j') as session:
            page_result = session.execute_write(self._blocks, blocks)
            return page_result
        
    def pages(self, pages: List[Page]):
        with self.driver.session(database='neo4j') as session:
            page_result = session.execute_write(self._pages, pages)
            return page_result
        
    def names(self, names: List[Name]):
        with self.driver.session(database='neo4j') as session:
            names_result = session.execute_write(self._names, names)
            return names_result
        
    def get_by_filter(self, query_filter: QueryFilter) -> List[Page]:
        with self.driver.session(database='neo4j') as session:
            result = session.execute_read(self._get_by_filter, query_filter)
            return result
        
    @staticmethod
    def _blocks(tx, blocks: List[Block]):
        if not blocks:
            return None

        neo4j_pages = [block.get_neo4j_properties() for block in blocks]
        merge_object = ', '.join([f'{key}: block.{key}' for key in Block.get_index_keys()])
        set_object = ', '.join([f'b.{key} = block.{key}' for key in Block.get_index_properties()])
        blocks_query = (
            'UNWIND $blocks as block '
            f'MERGE (b: Block {{{merge_object}}}) '
            'ON CREATE '
            f'SET {set_object} '
            'ON MATCH '
            f'SET {set_object} '
        )

        return tx.run(blocks_query, pages=neo4j_pages)
    
    @staticmethod
    def _pages(tx, pages: List[Page]):
        if not pages:
            return None

        neo4j_pages = [page.get_neo4j_properties() for page in pages]
        block_merge_object = ', '.join([f'{key}: block.{key}' for key in Block.get_index_keys()])
        merge_object = ', '.join([f'{key}: page.{key}' for key in Page.get_index_keys()])
        set_object = ', '.join([f'p.{key} = page.{key}' for key in Page.get_index_properties()])
        pages_query = (
            'UNWIND $pages as page '
            f'MERGE (p: Page {{{merge_object}}}) '
            'ON CREATE '
            f'SET {set_object} '
            'ON MATCH '
            'CALL { '
            'WITH p '
            f'SET {set_object} '
            'WITH p '
            'MATCH (p)-[]-(old_block: Block) '
            'DETACH DELETE old_block '
            '} '
            'WITH p, page '
            'UNWIND page.consists as block '
            f'MATCH (b: Block {{{block_merge_object}}}) '
            'MERGE (p)-[:Consists]->(b) '
        )

        return tx.run(pages_query, pages=neo4j_pages)
    
    @staticmethod
    def _names(tx, names: List[Name]):
        if not names:
            return None

        neo4j_names = [name.get_neo4j_properties() for name in names]
        page_merge_object = ', '.join([f'{key}: page.{key}' for key in Page.get_index_keys()])
        merge_object = ', '.join([f'{key}: name.{key}' for key in Name.get_index_keys()])
        set_object = ', '.join([f'n.{key} = name.{key}' for key in Name.get_index_properties()])
        names_query = (
            'UNWIND $names as name '
            f'MERGE (n: Name {{{merge_object}}}) '
            'ON CREATE '
            f'SET {set_object} '
            'WITH n, name '
            'UNWIND name.mentioned as mentioned '
            f'MATCH (p: Page {{{page_merge_object}}}) '
            'WITH n, p '
            'MERGE (n)-[:Mentioned]->(p) '
        )

        return tx.run(names_query, names=neo4j_names)
        
    @staticmethod
    def _parse_record_pages(records: List[Record]) -> List[Page]:
        pages: List[Page] = []
        for record in records:
            page_node = record.get('page')
            page_id = page_node.get('id')
            page_integration = page_node.get('integration')

            consists_list = []
            for block_node in record.get('blocks', []):
                block_id = block_node.get('id')
                block_label = block_node.get('label')
                block_content = block_node.get('content')
                last_updated_timestamp = block_node.get(
                    'last_updated_timestamp')
                block = Block(
                    id=block_id,
                    embedding=None,
                    label=block_label,
                    content=block_content,
                    last_updated_timestamp=last_updated_timestamp
                )
                consists = Consists(block)
                consists_list.append(consists)

            page = Page(
                id=page_id,
                integration=page_integration,
                consists=consists_list
            )
            pages.append(page)
        return pages

    # TODO: make more efficient by using params instead of injecting
    @staticmethod
    def _get_by_filter(tx, query_filter: QueryFilter) -> List[Page]:
        if not query_filter or not query_filter.library:
            return None

        query_wheres = []

        if query_filter.library:
            query_wheres.append(
                'page.library = $library AND block.library = $library')

        if query_filter.page_filter:
            page_filter = query_filter.page_filter
            if page_filter.ids:
                query_wheres.append(
                    f'page.id IN {list(page_filter.ids)}')
            if page_filter.integrations:
                query_wheres.append(
                    f'(page.integration IN {list(page_filter.integrations)})')
            if page_filter.time_range:
                query_wheres.append(
                    f'(page.timestamp >= {page_filter.time_range[0]} AND page.timestamp <= {page_filter.time_range[1]})')

        content_filter = ''
        if query_filter.block_filter:
            block_filter = query_filter.block_filter
            if block_filter.ids:
                query_wheres.append(
                    f'(block.id IN {list(block_filter.ids)})')
            if block_filter.labels:
                query_wheres.append(
                    f'(block.label IN {list(block_filter.labels)})')
            if block_filter.time_range:
                query_wheres.append(
                    f'(block.timestamp >= {block_filter.time_range[0]} AND block.timestamp <= {block_filter.time_range[1]})')
            if block_filter.regex_matches and query_filter.name_filter:
                content_regexes = []
                regex_matches = []
                counter = 0
                for regex_match in block_filter.regex_matches:
                    matches = []
                    if regex_match.label:
                        matches.append(f'rblock.label = "{regex_match.label}"')
                    matches.append(f'rblock.content =~ regex_{counter}')

                    content_regex = f'({" AND ".join(matches)})'
                    content_regexes.append(content_regex)
                    replaced_regex_match = regex_match.match \
                        .replace('"', '\\"') \
                        .replace('{', '\\{') \
                        .replace('}', '\\}') \
                        .replace(ContentMatch.get_entity_id_match_placeholder(), '" + name.id + "')
                    regex_match = f'"{replaced_regex_match}" AS regex_{counter}'
                    regex_matches.append(regex_match)
                    counter += 1
                content_filter = (
                    f'WITH name, page, block, {", ".join(regex_matches)} '
                    'MATCH (name)-[:Mentioned]->(page)-[:Consists]->(rblock:Block) '
                    f'WHERE {" OR ".join(content_regexes)} '
                )

        name_match = ''
        group_bys = []
        if query_filter.name_filter:
            name_match = '(name:Name)-[:Mentioned]->'
            name_filter = query_filter.name_filter
            query_wheres.append('name.library = $library')
            group_bys.append('COUNT(name.id) AS names_count')
            if name_filter.ids:
                query_wheres.append(f'(name.id IN {list(name_filter.ids)})')
            if name_filter.names:
                contains = []
                for name in name_filter.names:
                    contains.append(
                        f'toLower(name.value) CONTAINS "{name.lower()}"')
                contains_sub_query = ' OR '.join(contains)
                query_wheres.append(f'({contains_sub_query})')

        order_by_query = ''
        order_by = ''
        if query_filter.order_by:
            order_by = query_filter.order_by
            if order_by.property and order_by.node:
                order_by = ', max(block.last_updated_timestamp) AS order_by'
                order_by_query = 'ORDER BY order_by'
                if query_filter.order_by.direction == OrderDirection.DESC:
                    order_by_query += ' DESC'

        limit_query = ''
        if query_filter.limit:
            limit = query_filter.limit
            if limit.offset:
                limit_query += f'SKIP {limit.offset}'
            if limit.count:
                limit_query = f'LIMIT {limit.count}'

        if len(limit_query) < 1:
            limit_query = 'LIMIT 50'

        if len(query_wheres) < 1:
            return None

        # TODO: make prettier
        additional_group_bys = ''
        if group_bys:
            additional_group_bys = ', ' + ', '.join(group_bys)
        follow_up_group_by = ''
        if len(group_bys) > 0:
            follow_up_group_by += ', names_count'
        if len(order_by) > 0:
            follow_up_group_by += ', order_by'
        query = (
            f'MATCH {name_match}(page:Page)-[:Consists]->(block:Block) '
            f'WHERE {" AND ".join(query_wheres)} '
            f'{content_filter} '
            f'WITH page, block{additional_group_bys}{order_by} '
            f'WITH page, COLLECT(block) AS blocks{follow_up_group_by} '
            f'RETURN page, blocks '
            f'{order_by_query} '
            f'{limit_query} '
        )
        print(f'[Neo4j]: Executing query... {query}')
        result = tx.run(query, library=query_filter.library)
        records = list(result)
        print('[Neo4j]: Query completed!')
        print(records)

        return Neo4j._parse_record_pages(records)
    