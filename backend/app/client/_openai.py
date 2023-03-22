from typing import Dict, Generator, List, Optional, Union

from openai import ChatCompletion, Completion, Embedding

TRIPLETS_SUFFIX = (
    'Text: {text}\n'
    'Triplets:\n'
)

TRIPLETS_SYSTEM_CONTENT = (
    'Some text is provided below. Given the text, extract '
    'knowledge triplets in the form of ([subject] [predicate] [object]). '
    'Avoid stopwords.\n'
    '---------------------\n'
    'Text: Alice is Bob\'s mother.\n'
    'Triplets:\n'
    '([Alice] [is mother of] [Bob])\n'
    'Text: Philz is a coffee shop founded in Berkeley in 1982.\n'
    'Triplets:\n'
    '([Philz] [is] [coffee shop])\n'
    '([Philz] [founded in] [Berkeley])\n'
    '([Philz] [founded in] [1982])\n'
    '---------------------\n'
)

class OpenAI:
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
        if not (self._api_key and prompt):
            return None
        
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
    
    def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = 'gpt-3.5-turbo',
        max_tokens: int = 1000,
        temperature: float = 0,
        top_p: int = None,
        n: int = 1,
        stop: Optional[Union[str, List[str]]] = None,
    ) -> Generator[str]:
        if not (self._api_key and messages and len(messages) > 0):
            return None

        response_stream = ChatCompletion.create(
            api_key=self._api_key,
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            n=n,
            stop=stop,
            stream=True
        )

        output: str = ''
        accumulated_tokens: int = 0
        for response in response_stream:
            choices: List[dict] = response.get('choices', None) if response else None
            if not choices or len(choices) == 0:
                continue

            for choice in choices:
                delta: dict = choice.get('delta', None) if choice else None
                streamed_output: dict = delta.get('content', None) if delta else None
                if not streamed_output:
                    continue
                output += streamed_output
                accumulated_tokens += len(streamed_output)
            if accumulated_tokens > 20:
                yield output
                accumulated_tokens = 0
        if accumulated_tokens > 0:
            yield output

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
    
    def triplets(self, text: str) -> str:
        if not (self._api_key and text):
            return None
        
        triplets_response = ChatCompletion.create(
            api_key=self._api_key,
            model='gpt-3.5-turbo',
            messages=[
                { 'role': 'system', 'content': TRIPLETS_SYSTEM_CONTENT },
                { 'role': 'user', 'content': TRIPLETS_SUFFIX.format(text=text) },
            ],
            temperature=0
        )
        triplets_choices = triplets_response.get('choices', None) if triplets_response else None
        message = triplets_choices[0].get('message', None) if triplets_choices and len(triplets_choices) > 0 else None
        triplets = message.get('content', None) if message else None
        return triplets
