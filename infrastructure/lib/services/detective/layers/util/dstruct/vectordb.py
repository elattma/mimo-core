from dataclasses import dataclass
from typing import Dict, List, Literal

from dstruct.model import BlockQuery
from external.pinecone_ import Pinecone

RowType = Literal['block', 'chunk', 'cluster']

@dataclass
class Row:
    library: str
    id: str
    embedding: List[float]
    date_day: str
    type: RowType
    label: str


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
                'metadata': {
                    'library': row.library,
                    'date_day': row.date_day,
                    'type': row.type,
                    'label': row.label,
                }
            })
        
        return self._db.upsert(vectors=vectors)

    def fetch(self, ids: List[str], library: str) -> Dict[str, List[float]]:
        fetch_response = self._db.fetch([self._keyed_id(id, library) for id in ids])
        map: Dict[str, List[float]] = {}
        for id, vector in fetch_response.items():
            map[id] = vector.get('values', None)
        return map
    
    def query(self,
              block_query: BlockQuery,
              library: str,
              top_k: int = 5,
              include_values: bool = False,
              type: RowType = None) -> Dict[str, List[float]]:
        if not (block_query and block_query.embedding and library):
            return None
        
        filter = {
            'library': library
        }
        if type:
            filter['type'] = {
                '$eq': type
            }

        if block_query:
            if block_query.absolute_time:
                date_day_filter = {}
                if block_query.absolute_time[0]:
                    date_day = block_query.absolute_time[0].strftime('%Y-%m-%d')
                    date_day_filter['$gte'] = date_day
                if block_query.absolute_time[1]:
                    date_day = block_query.absolute_time[1].strftime('%Y-%m-%d')
                    date_day_filter['$lte'] = date_day
                filter['date_day'] = date_day_filter
            if block_query.labels:
                filter['id'] = {
                    '$in': block_query.labels
                }

        query_response = self._db.query(
            embedding=block_query.embedding,
            filter=filter,
            top_k=top_k,
            include_metadata=False,
            include_values=include_values
        )
        map: Dict[str, List[float]] = {}
        for raw_row in query_response:
            map[raw_row.get('id')] = raw_row.get('values', None)
        return map
    