from dataclasses import dataclass
from typing import List

from openai import ChatCompletion, Completion, Embedding


@dataclass
class KnowledgeTriplet:
    subject: str
    predicate: str
    object: str

def get_embedding(api_key: str, text: str) -> str:
    if not (api_key and text):
        return None
    
    response = Embedding.create(
        input=text,
        model='text-embedding-ada-002',
        api_key=api_key
    )
    data = response.get('data', None) if response else None
    first = data[0] if data and len(data) > 0 else None
    embedding = first.get('embedding', None) if first else None
    return embedding

# TODO: refactor to llm class
def summarize(api_key: str, text: str):
    if not (api_key and text):
        return None
    
    summary_response = ChatCompletion.create(
        api_key=api_key,
        model='gpt-3.5-turbo',
        messages=[
            { 'role': 'system', 'content': 'You are an assistant who summarizes.' },
            { 'role': 'user', 'content': text },
            { 'role': 'user', 'content': 'Given the above text document, describe what the document is and summarize the main points.' }
        ],
        temperature=0
    )
    summary_choices = summary_response.get('choices', None) if summary_response else None
    message = summary_choices[0].get('message', None) if summary_choices and len(summary_choices) > 0 else None
    summary = message.get('content', None) if message else None
    return summary

def get_knowledge_triplets(api_key: str, text: str, named_entities: List[str] = None) -> List[KnowledgeTriplet]:
    if not (api_key and text):
        return None
    
    summary = summarize(api_key=api_key, text=text)
    
    triplets_prompt = (
        'Some text is provided below. Given the text, extract '
        'knowledge triplets in the form of ([subject] [predicate] [object]). Avoid stopwords.\n'
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
        f'Text: {summary}\n'
        'Triplets:\n'
    )
    triplets_response = Completion.create(
        model='text-davinci-003',
        prompt=triplets_prompt,
        api_key=api_key,
        temperature=0,
        max_tokens=512
    )
    triplets_choices = triplets_response.get('choices', None) if triplets_response else None
    triplets: str = triplets_choices[0].get('text', None) if triplets_choices and len(triplets_choices) > 0 else None

    if not triplets:
        return None
    
    knowledge_triplets: List[KnowledgeTriplet] = []
    for triplet in triplets.strip().split('\n'):
        triplet_components = triplet[2:-2].split('] [')
        if len(triplet_components) != 3:
            print('skipping!')
            continue
        
        s, p, o = triplet_components
        knowledge_triplets.append(KnowledgeTriplet(subject=s.strip().lower(), predicate=p.strip().lower(), object=o.strip().lower()))
    
    print(knowledge_triplets)
    return knowledge_triplets