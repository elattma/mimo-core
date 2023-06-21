from dataclasses import dataclass
from typing import List, Literal

from external.pinecone_ import Pinecone


@dataclass
class Row:
    id: str
    embedding: List[float]
    library: str
    date_day: str
    type: Literal['block', 'chunk', 'cluster']
    label: str

    def as_dict_metadata(self):
        return {
            'library': self.library,
            'date_day': self.date_day,
            'type': self.type,
            'label': self.label,
        }


class VectorDB:
    def __init__(self, db: Pinecone) -> None:
        self._db = db
        
    def _keyed_id(self, id: str, library: str):
        return f'{library}#{id}'
    
    def delete(self, ids: List[str], library: str) -> bool:
        return self._db.delete([self._keyed_id(id, library) for id in ids])

    def upsert(self, rows: List[Row]):
        if not rows:
            return None
        
        vectors = []
        for row in rows:
            vectors.append({
                'id': self._keyed_id(row.id, row.library),
                'values': row.embedding,
                'metadata': row.as_dict_metadata()
            })
        
        return self._db.upsert(vectors=vectors)

    def fetch(self, ids: List[str], library: str):
        return self._db.fetch([self._keyed_id(id, library) for id in ids])
