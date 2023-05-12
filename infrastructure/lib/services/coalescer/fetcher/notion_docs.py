# from dataclasses import dataclass
# from typing import Any, List

# import requests
# from app.fetcher.base import (Chunk, DiscoveryResponse, Fetcher, FetchResponse,
#                               Filter, Item)


# @dataclass
# class NotionData:
#     chunks: List[Chunk]
#     children_block_ids: List[str]
#     cursor: str = None

# class Notion(Fetcher):
#     _INTEGRATION = 'notion'

#     def get_auth_type(self) -> str:
#         return 'oauth'
    
#     def get_auth_attributes(self) -> dict:
#         return {
#             'authorize_endpoint': 'https://api.notion.com/v1/oauth/token'
#         }

#     def discover(self, filter: Filter = None) -> DiscoveryResponse:
#         print('notion discovery!')

#         response = requests.post(
#             'https://api.notion.com/v1/search', 
#             headers={
#                 'Authorization': f'Bearer {self.auth.access_token}',
#                 'Content-Type': 'application/json',
#                 'Notion-Version': '2022-06-28'
#             },
#             json={
#                 'filter': {
#                     'value': 'page',
#                     'property': 'object',
#                 },
#                 'start_cursor': filter.next_token,
#                 'sort': {
#                     'direction': 'ascending',
#                     'timestamp': 'last_edited_time'
#                 }
#             }
#         )

#         discovery_response = response.json() if response else None
#         results = discovery_response.get('results', None) if discovery_response else None
#         if not results:
#             print('failed to get results')
#             return None
        
#         return DiscoveryResponse(
#             integration=self._INTEGRATION, 
#             icon=self.get_icon(),
#             items=[Item(
#                 id=result.get('id', None),
#                 title=result.get('id', None),
#                 link=result.get('url', None),
#                 preview=None
#             ) for result in results],
#             next_token=discovery_response.get('next_cursor', None) if discovery_response else None
#         )
    
#     def _get_block(self, id: str) -> NotionData:
#         block_ids = []
#         chunks: List[Chunk] = []
#         try:
#             cursor: str = None
#             while True:
#                 response = requests.get(
#                     f'https://api.notion.com/v1/blocks/{id}/children',
#                     headers={
#                         'Authorization': f'Bearer {self.auth.access_token}',
#                         'Content-Type': 'application/json',
#                         'Notion-Version': '2022-06-28'
#                     }
#                 )

#                 load_response = response.json() if response else None
#                 if not load_response:
#                     print('failed to get load response')
#                     return

#                 type = load_response.get('type', None) if load_response else None
#                 if type == 'paragraph':
#                     obj = load_response.get(type, None) if load_response and type else None
#                     rich_texts = obj.get('rich_text', None) if obj else None
#                     for rich_text in rich_texts:
#                         text = rich_text.get('text', None) if rich_text else None
#                         content = text.get('content', None) if text else None
#                         if content:
#                             chunks.append(Chunk(content=content))

#                 has_children = load_response.get('has_children', None) if load_response else None
#                 if has_children:
#                     children = load_response.get('children', None) if load_response else None
#                     if children:
#                         for child in children:
#                             block_ids.append(child.get('id', None) if child else None)
#                 cursor = load_response.get('next_cursor', None) if load_response else None
#                 if not cursor:
#                     break
            
#         except Exception as e:
#             print(e)
#             return None #TODO: fix


#     def fetch(self, id: str) -> FetchResponse:
#         print('notion load!')

#         block_ids: str = [id]
#         chunks: List[Chunk] = []
#         while len(block_ids) > 0:
#             block_id = block_ids.pop(0)
#             if not block_id:
#                 continue

#             data = self._get_block(block_id)
#             if data and len(data.children_block_ids):
#                 block_ids[0:0] = data.children_block_ids
#             if len(data.chunks):
#                 chunks.append('\n\n'.join(data.chunks))

#         return FetchResponse(
#             integration=self._INTEGRATION,
#             chunks=self.merge_split_chunks(chunks=chunks)
#         )
