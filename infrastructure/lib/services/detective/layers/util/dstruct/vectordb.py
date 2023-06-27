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
    
    def _unkeyed_id(self, id: str):
        return id.split('#')[1]
    
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

    def fetch(self, ids: List[str], library: str) -> List[Row]:
        fetch_response = self._db.fetch([self._keyed_id(id, library) for id in ids])
        rows: List[Row] = []
        for id, vector in fetch_response.items():
            metadata = vector.get('metadata', {})
            rows.append(Row(
                id=self._unkeyed_id(id),
                library=library,
                embedding=vector.get('values', None),
                date_day=metadata.get('date_day', None),
                type=metadata.get('type', None),
                label=metadata.get('label', None)
            ))
        return rows
    
    def query(self,
              block_query: BlockQuery,
              library: str,
              top_k: int = 5,
              include_values: bool = False,
              type: RowType = None) -> List[Row]:
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
            if block_query.absolute_time_end:
                filter['date_day'] = {
                    '$lte': block_query.absolute_time_end
                }
            if block_query.absolute_time_start:
                date_day = filter.get('date_day', {})
                date_day['$gte'] = block_query.absolute_time_start
                filter['date_day'] = date_day
            if block_query.labels:
                filter['id'] = {
                    '$in': block_query.labels
                }

        query_response = self._db.query(
            embedding=block_query.embedding,
            filter=filter,
            top_k=top_k,
            include_metadata=True,
            include_values=include_values
        )
        rows: List[Row] = []
        for raw_row in query_response:
            metadata = raw_row.get('metadata', {})
            rows.append(Row(
                id=self._unkeyed_id(raw_row['id']),
                library=library,
                embedding=raw_row.get('values', None),
                date_day=metadata.get('date_day', None),
                type=metadata.get('type', None),
                label=metadata.get('label', None)
            ))
        return rows
    