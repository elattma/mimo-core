from openai import Embedding


def get_embedding(api_key: str, text: str) -> str:
    if not text:
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
