import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Set, Type, Union

from .util import date_string_to_date_day, get_today_date_string


@dataclass
class Request:
    encoding_name: str
    text: str
    embedding: List[float]


class QueryComponent(ABC):
    '''An abstract class for a component of a Query.'''
    @classmethod
    @abstractmethod
    def from_llm_response(cls, s: str) -> 'QueryComponent':
        '''Converts a string generated by an LLM to a QueryComponent.'''
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def description_for_prompt() -> str:
        '''Returns a description of the component for use in a prompt.'''
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def json_for_prompt() -> str:
        '''Returns how the component should be represented in the prompt's
        sample JSON.'''
        raise NotImplementedError

    @classmethod
    def load_components_from_json(
        cls,
        json_: Dict
    ) -> Dict[Type['QueryComponent'], 'QueryComponent']:
        components = {}
        for key, value in json_.items():
            try:
                component_class = cls.get_component_from_json_key(key)
            except ValueError:
                print(
                    f'LLM produced invalid query component: {key}'.replace(
                        '\n',
                        '\r'
                    )
                )
                continue
            component = component_class.from_llm_response(value)
            if component:
                components[component_class] = component
        return components

    @classmethod
    def get_component_descriptions(cls) -> str:
        '''Returns a description of all components for use in a prompt.'''
        component_descriptions = [c.description_for_prompt() for c in
                                  cls.get_components_list()]
        return '\n'.join(component_descriptions)

    @classmethod
    def get_json_schema(cls) -> str:
        '''Returns a JSON schema for all components for use in a prompt.'''
        json_parts = [c.json_for_prompt()
                      for c in cls.get_components_list()]
        return '{\n' + ',\n'.join(json_parts) + '\n}'

    @staticmethod
    def get_component_from_json_key(key: str) -> Type['QueryComponent']:
        lookup = {
            'concepts': Concepts,
            'page_participants': PageParticipants,
            'time_frame': AbsoluteTimeFilter,
            'time_sort': RelativeTimeFilter,
            'count': Count,
            'sources': PageTypeFilter,
            'search_method': SearchMethod,
            'blocks_to_search': BlocksToSearch,
            'return_type': ReturnType,
            'blocks_to_return': BlocksToReturn
        }
        if key not in lookup:
            raise ValueError(f'Invalid key: {key}')
        return lookup[key]

    @staticmethod
    def get_components_list() -> List[Type['QueryComponent']]:
        '''Returns a list of all components as QueryComponent objects.'''
        return [
            Concepts,
            PageParticipants,
            AbsoluteTimeFilter,
            RelativeTimeFilter,
            Count,
            IntegrationsFilter,
            SearchMethod,
            BlocksToSearch,
            ReturnType,
            BlocksToReturn
        ]
    

@dataclass
class Concepts(QueryComponent):
    '''Suggests semantically important concepts from the request.'''
    values: List[str]

    @classmethod
    def from_llm_response(cls, llm_response: List[str]) -> 'Concepts':
        if not Concepts._validate_llm_response(llm_response):
            print('Failed to create Concepts from LLM response:\n')
            print(str(llm_response).replace('\n', '||'))
            return None
        return cls(llm_response)

    @staticmethod
    def description_for_prompt() -> str:
        return ('concepts: A list of independent concepts that are '
                'semantically important. These concepts are extracted from '
                'the Request. They should capture whole ideas, not just '
                'individual words. For example, if the request is "Documents '
                'about the role of tech in the office", the concepts should '
                'be ["role of tech in the office"], not ["role", "tech", '
                '"office"].')

    @staticmethod
    def json_for_prompt() -> str:
        return ' "concepts": string[]'

    @staticmethod
    def _validate_llm_response(llm_response: List[str]) -> bool:
        return bool(llm_response)


class PageParticipantRole(Enum):
    AUTHOR = 'author'
    RECIPIENT = 'recipient'
    UNKNOWN = 'unknown'


@dataclass
class PageParticipant:
    name: str
    role: PageParticipantRole


@dataclass
class PageParticipants(QueryComponent):
    '''Enforces that only results linked to these names are considered.'''
    values: List[PageParticipant]

    @classmethod
    def from_llm_response(
        cls,
        llm_response: List[Dict[str, str]]
    ) -> 'PageParticipants':
        # llm_response should be a list of dictionaries with each entry
        # containing keys "name" and "role" that map to strings
        if not PageParticipants._validate_llm_response(llm_response):
            print('Failed to create PageParticipants from LLM response:\n')
            print(str(llm_response).replace('\n', '||'))
            return None
        values = []
        for item in llm_response:
            name = item['name']
            role = item['role']
            if name and role:
                values.append(PageParticipant(
                    name=name,
                    role=PageParticipantRole(role)
                ))
        return cls(values) if values else None

    @staticmethod
    def description_for_prompt() -> str:
        return ('page_participants: A list of entities, e.g. people or '
                'organizations, that are linked to the '
                'information you are searching for. They should be paired '
                'with their relationship to the information.')

    @staticmethod
    def json_for_prompt() -> str:
        return (' "page_participants": {\n'
                '  "name": string,\n'
                '  "role": "author" OR "recipient" OR "unknown"\n'
                ' }[]')

    @staticmethod
    def _validate_llm_response(
        llm_response: List[Dict[str, str]]
    ) -> bool:
        if not llm_response:
            return None
        for item in llm_response:
            if not (item and 'name' in item):
                return False
            if ('role' not in item or not
                (item['role'] == PageParticipantRole.AUTHOR.value
                 or item['role'] == PageParticipantRole.RECIPIENT.value)):
                item['role'] = PageParticipantRole.UNKNOWN.value
        return True


@dataclass
class AbsoluteTimeFilter(QueryComponent):
    '''Enforces that only results within this time frame are considered. e.g.
    "between 2020 and 2022", "in the last 5 days"'''
    start: int = None
    end: int = None

    @classmethod
    def from_llm_response(
        cls,
        llm_response: Dict[str, str]
    ) -> 'AbsoluteTimeFilter':
        # llm_response should be a dictionary with two keys: 'start' and
        # 'end'. Each value should be a string in the format 'YYYY-MM-DD'.
        start = llm_response.get('start', None)
        end = llm_response.get('end', None)
        start_valid = cls._validate_date(start)
        end_valid = cls._validate_date(end)
        if not (start_valid or end_valid):
            print('Failed to create AbsoluteTimeFilter from LLM response:\n')
            print(str(llm_response).replace('\n', '||'))
            return None
        start = date_string_to_date_day(
            llm_response['start']
        ) if start_valid else None
        end = date_string_to_date_day(
            llm_response['end']
        ) if end_valid else None
        return cls(start, end)

    @staticmethod
    def description_for_prompt() -> str:
        current_date = get_today_date_string()
        return ('time_frame: Include time_frame if the Request implies that '
                'the requested information was created within a specific '
                f'time frame. It is currently {current_date}.')

    @staticmethod
    def json_for_prompt() -> str:
        return (' "time_frame": {\n'
                '  "start": string,\n'
                '  "end": string\n'
                ' }')

    @staticmethod
    def _validate_date(maybe_date: str) -> bool:
        try:
            return re.match(r'\d{4}-\d{2}-\d{2}', str(maybe_date))
        except:
            return False


@dataclass
class RelativeTimeFilter(QueryComponent):
    '''Enforces relative ordering of results based on time. e.g.
    "most recent", "oldest"'''
    ascending: bool

    @classmethod
    def from_llm_response(
        cls,
        llm_response: Dict[str, bool]
    ) -> 'RelativeTimeFilter':
        # llm_response should be a dictionary with two keys: 'ascending' and
        # 'count'. The value of 'ascending' should be a boolean and the value
        # of 'count' should be an integer.
        if not RelativeTimeFilter._validate_llm_response(llm_response):
            print('Failed to create RelativeTimeFilter from LLM response:\n')
            print(str(llm_response).replace('\n', '||'))
            return None
        ascending = llm_response['ascending']
        return cls(ascending)

    @staticmethod
    def description_for_prompt() -> str:
        return ('time_sort: Include a time_sort if the Request is requesting '
                'information based on a relative ordering of time.')

    @staticmethod
    def json_for_prompt() -> str:
        return (' "time_sort": {\n'
                '  "ascending": boolean\n'
                ' }')

    @staticmethod
    def _validate_llm_response(
        llm_response: Dict[str, Union[bool, int]]
    ) -> bool:
        return (llm_response and 'ascending' in llm_response
                and isinstance(llm_response['ascending'], bool))


@dataclass
class Count(QueryComponent):
    '''Enforces a limit on the number of results that are returned.'''
    value: int

    @classmethod
    def from_llm_response(cls, llm_response: int) -> 'Count':
        if not isinstance(llm_response, int) or llm_response < 1:
            print('Failed to create Count from LLM response:\n')
            print(str(llm_response).replace('\n', '||'))
            return None
        return cls(llm_response)

    @staticmethod
    def description_for_prompt() -> str:
        return ('count: Include count if the Request is requesting a '
                'specific number of results.')

    @staticmethod
    def json_for_prompt() -> str:
        return ' "count": integer'


@dataclass
class PageTypeFilter(QueryComponent):
    '''Enforces that only results from these page types are considered'''
    types: List[str]

    @classmethod
    def from_llm_response(cls, llm_response: List[str]) -> 'PageTypeFilter':
        if not llm_response:
            return None
        try:
            types = types
        except ValueError:
            print('Failed to create PageTypeFilter from LLM response:\n')
            print(str(llm_response).replace('\n', '||'))
            return None
        return cls(types)

    @staticmethod
    def description_for_prompt() -> str:
        data_sources = ', '.join()
        data_sources = f'[{data_sources}]'
        return ('sources: Identify any data sources that are referenced in '
                'the Request. The possible data sources are: '
                f'{data_sources}.')

    @staticmethod
    def json_for_prompt() -> str:
        return ' "sources": string[]'


class SearchMethodValue(Enum):
    RELEVANT = 'relevant'
    EXACT = 'exact'


@dataclass
class SearchMethod(QueryComponent):
    '''Enforces the method by which results are returned.\n
    Examples:\n
    "all emails from Troy" => "exact"\n
    "emails from Troy related to the budget" => "relevant"'''
    value: SearchMethodValue

    @classmethod
    def from_llm_response(cls, llm_response: str) -> 'SearchMethod':
        try:
            value = SearchMethodValue(llm_response)
        except ValueError:
            print('Failed to create SearchMethod from LLM response:\n')
            print(str(llm_response).replace('\n', '||'))
            return None
        return cls(value)

    @staticmethod
    def description_for_prompt() -> str:
        return ('search_method: Determine whether the Request is looking '
                'for exact information or the most relevant information.')

    @staticmethod
    def json_for_prompt() -> str:
        return ' "search_method": "exact" OR "relevant"'
    

class ReturnTypeValue(Enum):
    PAGES = 'pages'
    BLOCKS = 'blocks'


@dataclass
class ReturnType(QueryComponent):
    value: ReturnTypeValue

    @staticmethod
    def from_llm_response(llm_response: str) -> 'ReturnType':
        try:
            value = ReturnTypeValue(llm_response)
        except ValueError:
            print('Failed to create ReturnType from LLM response:\n')
            print(str(llm_response).replace('\n', '||'))
            return None
        return ReturnType(value)

    @staticmethod
    def description_for_prompt() -> str:
        return ('return_type: If the Request is explicitly seeking an '
                'entire page, select "pages". Otherwise, select "blocks". '
                'The pages associated with each data source are: (crm: '
                'Account) (customer_support: Ticket) (documents: Document) '
                '(email: Email Thread)')

    @staticmethod
    def json_for_prompt() -> str:
        return ' "return_type": "pages" OR "blocks"'
    

class Block(Enum):
    BODY = 'body'
    COMMENT = 'comment'
    CONTACT = 'contact'
    DEAL = 'deal'
    MEMBER = 'member'
    SUMMARY = 'summary'
    TITLE = 'title'


@dataclass
class BlocksFilter(QueryComponent, ABC):
    '''Abstract class for blocks filters.'''
    blocks: List[Block]

    @classmethod
    def from_llm_response(cls, llm_response: List[str]) -> 'BlocksFilter':
        if not llm_response:
            return None
        try:
            blocks = [Block(block) for block in llm_response]
        except ValueError:
            print('Failed to create BlockFilter from LLM response:\n')
            print(str(llm_response).replace('\n', '||'))
            return None
        return cls(blocks)
    
    @staticmethod
    def get_block_descriptions() -> str:
        return ('"body": The body of the page, e.g. the text in a '
                'Microsoft Word document.\n'
                '"comment": A comment on the page, e.g. a comment on a Jira '
                'ticket.\n'
                '"contact": A contact associated with an account in a CRM.\n'
                '"deal": A deal associated with an account in a CRM.\n'
                '"member": A list of members associated with the page, e.g. '
                'the author, recipients, etc.\n'
                '"summary": A summary of the page.\n'
                '"title": The title of the page.')


@dataclass
class BlocksToSearch(BlocksFilter):
    '''Enforces that only these blocks are searched.'''
    @staticmethod
    def description_for_prompt() -> str:
        block_names = ', '.join([f'"{block.value}"' for block in Block])
        block_names = '[' + block_names + ']'
        return (
            'blocks_to_search: A list of blocks to search. Used if you want '
            'to search for information based on specific blocks. The '
            f'possible blocks are: {block_names}'
        )

    @staticmethod
    def json_for_prompt() -> str:
        return ' "blocks_to_search": string[]'


@dataclass
class BlocksToReturn(BlocksFilter):
    '''Enforces that only these blocks are returned.'''
    @staticmethod
    def description_for_prompt() -> str:
        block_names = ', '.join([f'"{block.value}"' for block in Block])
        block_names = '[' + block_names + ']'
        return (
            'blocks_to_return: A list of blocks to return. Used if '
            'it is explicitly specified that the results should be '
            f'certain block type(s). The possible blocks are: {block_names}'
        )

    @staticmethod
    def json_for_prompt() -> str:
        return ' "blocks_to_return": string[]'
    

@dataclass
class PageIds(QueryComponent):
    values: Set[str]

    @classmethod
    def from_llm_response() -> 'PageIds':
        raise NotImplementedError
    
    @staticmethod
    def description_for_prompt() -> str:
        raise NotImplementedError
    
    @staticmethod
    def json_for_prompt() -> str:
        raise NotImplementedError


@dataclass
class Query:
    components: Dict[Type[QueryComponent], QueryComponent]
    request: Request = None

    @classmethod
    def from_string_and_request(cls, s: str, request: Request) -> 'Query':
        try:
            match = re.search(r'{[\s\S]*}', s, re.DOTALL)
            query_json = json.loads(match.group(0))
            components = QueryComponent.load_components_from_json(query_json)
            return cls(components, request)
        except Exception as e:
            print('[Query] Failed to parse query.', e, sep='\n')
            return cls({}, request)
