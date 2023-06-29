from typing import Dict, Generator, List

from auth.base import AuthType
from fetcher.base import Fetcher, StreamData

DISCOVERY_ENDPOINT = 'https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages'
GET_THREADS_ENDPOINT = 'https://graph.microsoft.com/v1.0/me/messages/{id}'

class MicrosoftMail(Fetcher):
    _INTEGRATION = 'microsoft_mail'
    
    def _get_supported_auth_types(self) -> List[AuthType]:
        return [AuthType.TOKEN_OAUTH2, AuthType.TOKEN_DIRECT, AuthType.BASIC]
    
    def discover(self) -> Generator[StreamData, None, None]:
        next_token = None
        params = {}
        limit = self._filter.limit if self._filter else None
        while True:
            if next_token:
                params.update({
                    '$skipToken': next_token
                })
            
            response = self.request(DISCOVERY_ENDPOINT, params=params)
            next_token = response.get('@odata.nextLink', None) if response else None
            threads: List[Dict] = response.get('value', None) if response else None

            for thread in threads:
                thread_id = thread.get('id', None) if thread else None
                if not thread_id:
                    continue
                yield StreamData(
                    name='email_thread',
                    id=thread_id,
                )
                if limit:
                    limit -= 1
                    if limit < 1:
                        return []

            if not next_token:
                break

    def fetch_thread(self, stream: StreamData) -> None:
        response = self.request(GET_THREADS_ENDPOINT.format(id=stream._id))
        message = response

        if not message:
            return

        author = message.get('from', {}).get('emailAddress', {}).get('address', '')
        title = message.get('subject', '')
        recipients = [recipient.get('emailAddress', {}).get('address', '') for recipient in message.get('toRecipients', [])]
        body = message.get('body', {}).get('content', '')

        from unstructured.partition.html import partition_html
        elements = partition_html(text=body)
        for element in elements:
            stream.add_unstructured_data('element', str(element))

        stream.add_structured_data_as_list('author', author)
        stream.add_unstructured_data('title', title)
        stream.add_structured_data_as_list('recipients', recipients)
        stream.add_structured_data('last_updated_timestamp', message.get('lastModifiedDateTime'))

    def fetch(self, stream: StreamData) -> None:
        if stream._name == 'email_thread':
            self.fetch_thread(stream)