# from dataclasses import dataclass
# from typing import List

# import requests
# from app.fetcher.base import (Chunk, DiscoveryResponse, Fetcher, FetchResponse,
#                               Filter, Item)


# @dataclass
# class SlackData:
#     chunks: List[Chunk] 
#     cursor: str = None

# class SlackMessaging(Fetcher):
#     _INTEGRATION = 'slack_messaging'

#     def get_auth_type(self) -> str:
#         return 'oauth'
    
#     def get_auth_attributes(self) -> dict:
#         return {
#             'authorize_endpoint': 'https://slack.com/api/oauth.v2.access'
#         }

#     def discover(self, filter: Filter = None) -> DiscoveryResponse:
#         print('slack discovery!')

#         filters = {}
#         if filter:
#             if filter.next_token:
#                 filters['cursor'] = filter.next_token
#             if filter.limit:
#                 filters['limit'] = filter.limit

#         response = requests.get(
#             'https://slack.com/api/conversations.list',
#             params={ **filters },
#             headers={
#                 'Authorization': f'Bearer {self.auth.access_token}'
#             }
#         )
#         discovery_response = response.json() if response else None
#         ok = discovery_response.get('ok', False) if discovery_response else False
#         if not ok:
#             print('failed to get slack conversations')
#             return None
        
#         channels = discovery_response.get('channels', [])
#         response_metadata = discovery_response.get('response_metadata', None)
#         next_token = response_metadata.get('next_cursor', None) if response_metadata else None

#         return DiscoveryResponse(
#             integration=self._INTEGRATION, 
#             icon=self.get_icon(),
#             items=[Item(
#                 id=channel['id'],
#                 title=channel['name'],
#                 link=f'https://slack.com/channels/{channel.id}',
#                 preview=None
#             ) for channel in channels],
#             next_token=next_token
#         )
    
#     def _get_replies(self, id: str, ts: str, cursor: str = None) -> SlackData:
#         response = requests.get(
#             f'https://slack.com/api/conversations.replies',
#             params={
#                 'channel': id,
#                 'ts': ts,
#                 'cursor': cursor
#             },
#             headers={
#                 'Authorization': f'Bearer {self.auth.access_token}'
#             }
#         )
#         load_response = response.json() if response else None
#         ok = load_response.get('ok', False) if load_response else False
#         if not ok:
#             print('failed to get slack conversation replies')
#             # TODO: add rate limit check etc.
#             return None
        
#         response_metadata = load_response.get('response_metadata', None)
#         next_token = response_metadata.get('next_cursor', None) if response_metadata else None
#         messages = load_response.get('messages', [])
#         chunks: List[Chunk] = []
#         for message in messages:
#             text = message.get('text', None) if message else None
#             user = message.get('user', None) if message else None
#             if not text or not user:
#                 continue

#             chunks.append(f'{user}: {text}. ')
#         return SlackData(chunks=chunks, cursor=next_token)
    
#     def _get_history(self, id: str, cursor: str = None) -> SlackData:
#         response = requests.get(
#             f'https://slack.com/api/conversations.history',
#             params={ 
#                 'channel': id, 
#                 'cursor': cursor 
#             },
#             headers={
#                 'Authorization': f'Bearer {self.auth.access_token}'
#             }
#         )
#         load_response = response.json() if response else None
#         ok = load_response.get('ok', False) if load_response else False
#         if not ok:
#             print('failed to get slack conversation history')
#             return None
        
#         response_metadata = load_response.get('response_metadata', None)
#         next_token = response_metadata.get('next_cursor', None) if response_metadata else None
#         messages = load_response.get('messages', [])
#         chunks: List[Chunk] = []
#         for message in messages:
#             message_ts = message.get('ts', None) if message else None
#             replies_cursor = None
#             while True:
#                 replies = self._get_replies(id, message_ts, replies_cursor)
#                 if not replies:
#                     print('failed to get slack conversation replies')
#                     break
#                 replies_cursor = replies.cursor
#                 chunks.extend(replies.chunks)
#                 if not replies_cursor:
#                     break

#         return SlackData(chunks=messages, cursor=next_token)

#     def fetch(self, id: str) -> FetchResponse:
#         print('slack load!')

#         history_cursor = None
#         chunks: List[Chunk] = []
#         while True:
#             history = self._get_history(id, history_cursor)
#             if not history:
#                 print('failed to get slack conversation history')
#                 break
#             history_cursor = history.cursor

#             chunks.extend(history.chunks)
#             if not history_cursor:
#                 break

#         return FetchResponse(
#             integration=self._INTEGRATION,
#             chunks=self.merge_split_chunks(chunks=chunks)
#         )
