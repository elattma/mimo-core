from typing import Dict, List, Optional, Union

from openai import ChatCompletion, Completion, Embedding


class OpenAIClient:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        
    def embed(self, text: str):
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
    
    def completion(
        self,
        prompt: str,
        model: str = 'text-davinci-003',
        max_tokens: int = 1000,
        temperature: float = 0,
        top_p: int = None,
        n: int = 1,
        stop: Optional[Union[str, List[str]]] = None,
    ):
        response = Completion.create(
            api_key=self._api_key,
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            n=n,
            stop=stop
        )

        choices = response.get('choices', None) if response else None
        text: str = choices[0].get('text', None) if choices and len(choices) > 0 else None
        return text
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = 'gpt-3.5-turbo',
        max_tokens: int = 1000,
        temperature: float = 0,
        top_p: int = None,
        n: int = 1,
        stop: Optional[Union[str, List[str]]] = None,
    ):
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