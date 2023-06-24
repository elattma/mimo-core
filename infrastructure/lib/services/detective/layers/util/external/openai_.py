import json
from typing import Dict, List, Optional, Union

from backoff import expo, full_jitter, on_exception
from openai import ChatCompletion, Embedding
from openai.error import APIConnectionError, RateLimitError


class OpenAI:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        
    @on_exception(expo, (RateLimitError, APIConnectionError), max_tries=5, jitter=full_jitter)
    def embed(self, text: str) -> List[float]:
        if not (self._api_key and text):
            return None
        
        response = Embedding.create(
            input=text,
            model='text-embedding-ada-002',
            api_key=self._api_key
        )
        data = response.get('data', None) if response else None
        first = data[0] if data and len(data) > 0 else None
        embedding = first.get('embedding', None) if first else None
        return embedding
    
    @on_exception(expo, (RateLimitError, APIConnectionError), max_tries=5, jitter=full_jitter)
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = 'gpt-3.5-turbo-0613',
        max_tokens: int = 2000,
        temperature: float = 0,
        top_p: int = None,
        n: int = 1,
        stop: Optional[Union[str, List[str]]] = None,
    ) -> str:
        if not messages:
            return None

        response = ChatCompletion.create(
            api_key=self._api_key,
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            n=n,
            stop=stop
        )
        choices: List[Dict] = response.get('choices', None) if response else None
        message: Dict = choices[0].get('message', None) if choices and len(choices) > 0 else None
        return message.get('content', None) if message else None
    
    @on_exception(expo, (RateLimitError, APIConnectionError), max_tries=5, jitter=full_jitter)
    def function_call(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, str]] = None,
        function_call: Dict[str, str] = None,
        model: str = 'gpt-4-0613',
        max_tokens: int = 2000,
        temperature: float = 0,
        top_p: int = None,
        n: int = 1,
        stop: Optional[Union[str, List[str]]] = None,
    ) -> Dict:
        if not messages:
            return None
        
        response = ChatCompletion.create(
            api_key=self._api_key,
            messages=messages,
            functions=functions,
            function_call=function_call,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            n=n,
            stop=stop
        )

        choices: List[Dict] = response.get('choices', None) if response else None
        arguments: str = choices[0].get('message', {}).get('function_call', {}).get('arguments', None) if choices else None
        return json.loads(arguments) if arguments else None

    def summarize(self, text: str):
        return self.chat_completion(
            messages=[{
                'role': 'system',
                'content': (
                    'Imagine you are a Data Genius who is able '
                    'to classify and understand any JSON data. '
                    'Summarize the provided JSON using simple sentences. '
                    'Preserve all important keywords, nouns, proper nouns, dates, concepts. '
                    'Do not use pronouns. Write as much as you need to preserve all important information!'
                )
            }, {
                'role': 'user',
                'content': text
            }]
        )
    
    def inferrable_entities(self, text: str):
        return self.function_call(
            messages=[{
                'role': 'system',
                'content': (
                    'Imagine you are a Data Genius who is able '
                    'to classify and understand any JSON data. '
                    'List all entities that can be inferred from the provided JSON data. '
                    'For example, if the JSON data contains a field "name", '
                    'then the entity "name" can be inferred from the JSON data.'
                )
            }, {
                'role': 'user',
                'content': text
            }]
        )