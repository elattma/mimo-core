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
        model: str = 'gpt-3.5-turbo',
        max_tokens: int = 1000,
        temperature: float = 0,
        top_p: int = None,
        n: int = 1,
        stop: Optional[Union[str, List[str]]] = None,
    ) -> str:
        if not (self._api_key and messages and len(messages) > 0):
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
        choices = response.get('choices', None) if response else None
        message = choices[0].get('message', None) if choices and len(choices) > 0 else None
        content = message.get('content', None) if message else None
        return content
    
    @on_exception(expo, (RateLimitError, APIConnectionError), max_tries=5, jitter=full_jitter)
    def summarize(self, text: str):
        if not (self._api_key and text):
            return None
        
        summary_response = ChatCompletion.create(
            api_key=self._api_key,
            model='gpt-3.5-turbo',
            messages=[
                { 'role': 'system', 'content': 'Summarize the text. Use simple sentences. Keep important keywords. Keep important nouns. Keep all proper nouns. Do not use pronouns.' },
                { 'role': 'user', 'content': text },
            ],
            temperature=0
        )
        summary_choices = summary_response.get('choices', None) if summary_response else None
        message = summary_choices[0].get('message', None) if summary_choices and len(summary_choices) > 0 else None
        summary = message.get('content', None) if message else None
        return summary
    