from dataclasses import dataclass
from datetime import datetime
from typing import List

from app.client._neo4j import (Chunk, Consists, Document, Entity, Neo4j,
                               Predicate)
from app.client._openai import OpenAI
from app.client._pinecone import Pinecone, Row, RowType
from ulid import ulid


@dataclass
class Triplet:
    subject: str
    predicate: str
    object: str

@dataclass
class IngestInput:
    owner: str
    integration: str
    document_id: str
    chunks: List[str]
    timestamp: int
    structured_triplets: List[Triplet] = None

@dataclass
class IngestResponse:
    succeeded: bool
    integration: str
    timestamp: int


MAX_TREE_CHUNKS_CHILDREN = 10


class Ingestor:
    def __init__(self, openai: OpenAI, neo4j: Neo4j, pinecone: Pinecone):
        self._openai = openai
        self._neo4j = neo4j
        self._pinecone = pinecone

    def _get_chunks(self, chunks: List[str]) -> List[Chunk]:
        if not (chunks and len(chunks) > 0):
            return []

        tree_chunks: List[Chunk] = []
        temp_chunks = chunks.copy()
        height = 0
        while len(temp_chunks) > 1:
            temp_chunks_len = len(temp_chunks)
            join_chunks = []
            for chunk in temp_chunks:
                chunk_embedding = self._openai.embed(chunk)
                tree_chunks.append(
                    Chunk(
                        id=ulid(),
                        embedding=chunk_embedding,
                        content=chunk,
                        height=height,
                    )
                )
            for i in range(0, temp_chunks_len, MAX_TREE_CHUNKS_CHILDREN):
                summary = self._openai.summarize(
                    "\n\n".join(
                        temp_chunks[
                            i : min(i + MAX_TREE_CHUNKS_CHILDREN, temp_chunks_len)
                        ]
                    )
                )
                join_chunks.append(summary)
            temp_chunks = join_chunks
            height += 1
        if len(temp_chunks) == 1:
            chunk_embedding = self._openai.embed(temp_chunks[0])
            tree_chunks.append(
                Chunk(
                    id=ulid(),
                    embedding=chunk_embedding,
                    content=temp_chunks[0],
                    height=height,
                )
            )
        return tree_chunks

    def _get_document(
        self, document_id: str, integration: str, chunks: List[Chunk]
    ) -> Document:
        document = Document(
            id=document_id,
            integration=integration,
            consists=[Consists(target=chunk) for chunk in chunks],
        )
        return document

    def _get_triplet_entities(
        self, document_id: str, chunk_id: str, chunk: str
    ) -> List[Entity]:
        triplets_string = self._openai.triplets(chunk)
        triplets: List[Triplet] = []
        for triplet in triplets_string.strip().split('\n'):
            triplet_components = triplet[2:-2].split('] [')
            if len(triplet_components) != 3:
                continue
            
            s, p, o = triplet_components
            triplets.append(Triplet(subject=s.strip().lower(), predicate=p.strip().lower(), object=o.strip().lower()))

        entities_dict: dict[str, Entity] = {}
        for triplet in triplets:
            triplet_id = ulid()
            triplet_embedding = self._openai.embed(
                text=f"{triplet.subject} {triplet.predicate} {triplet.object}"
            )

            object_entity = Entity(id=triplet.object, type='gpt-3.5-turbo')

            predicate = Predicate(
                id=triplet_id,
                embedding=triplet_embedding,
                text=triplet.predicate,
                chunk=chunk_id,
                document=document_id,
                target=object_entity,
            )

            if triplet.subject not in entities_dict:
                entities_dict[triplet.subject] = Entity(
                    id=triplet.subject,
                    type='gpt-3.5-turbo',
                    predicates=[predicate],
                )
            else:
                entities_dict[triplet.subject].predicates.append(predicate)

        return entities_dict.values()

    def _squash_triplet_entities(self, triplets: List[Entity]) -> List[Entity]:
        entities_dict: dict[str, Entity] = {}
        for triplet in triplets:
            if triplet.id not in entities_dict:
                entities_dict[triplet.id] = triplet
            else:
                entities_dict[triplet.id].predicates.extend(triplet.predicates)
        return entities_dict.values()

    def ingest(self, input: IngestInput) -> IngestResponse:
        date_day = datetime.utcfromtimestamp(input.timestamp).strftime('%Y%m%d')

        succeeded = True
        try:
            document = self._get_document(
                document_id=input.document_id,
                integration=input.integration,
                chunks=self._get_chunks(input.chunks),
            )
            triplet_entities = []
            for chunk in document.consists:
                if chunk.target.height == 0:
                    continue

                # triplet entities only for non raw chunks
                entities = self._get_triplet_entities(
                    document_id=document.id,
                    chunk_id=chunk.target.id,
                    chunk=chunk.target.content,
                )
                triplet_entities.extend(entities)

            triplet_entities = self._squash_triplet_entities(triplet_entities)
            pinecone_response = self._pinecone_write(
                owner=input.owner, document=document, entities=triplet_entities, date_day=date_day              
            )
            neo4j_response = self._neo4j_write(
                owner=input.owner,
                documents=[document],
                entities=triplet_entities,
                timestamp=input.timestamp,
            )

            print(pinecone_response)
            print(neo4j_response)
        except Exception as e:
            print(e)
            succeeded = False

        return IngestResponse(
            succeeded=succeeded,
            integration=input.integration,
            timestamp=input.timestamp,
        )

    def _pinecone_write(
        self, owner: str, document: Document, entities: List[Entity], date_day: int
    ) -> bool:
        rows: List[Row] = []
        for chunk in document.consists:
            chunk_row = Row(
                id=chunk.target.id,
                embedding=chunk.target.embedding,
                owner=owner,
                integration=document.integration,
                document_id=document.id,
                type=RowType.CHUNK,
                date_day=date_day,
                leaf=chunk.target.height == 0,
            )
            rows.append(chunk_row)

        for entity in entities:
            for triplet in entity.predicates:
                triplet_row = Row(
                    id=triplet.id,
                    embedding=triplet.embedding,
                    owner=owner,
                    integration=document.integration,
                    document_id=triplet.document,
                    type=RowType.TRIPLET,
                    date_day=date_day,
                    leaf=False
                )
                rows.append(triplet_row)

        return self._pinecone.upsert(rows)

    def _neo4j_write(
        self,
        entities: List[Entity],
        documents: List[Document],
        owner: str,
        timestamp: int,
    ) -> bool:
        return self._neo4j.create_entities(
            entities=entities, documents=documents, owner=owner, timestamp=timestamp
        )

MAX_CHUNK_SIZE = 600
MAX_CHUNK_OVERLAP = 50

def __merge_chunks(self, chunks: List[Chunk]) -> Chunk:
    return Chunk(content="\n\n".join([chunk.content for chunk in chunks]).strip())

def merge_split_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
    if not chunks or len(chunks) < 1:
        return None
    final_chunks: List[Chunk] = []
    temporary_chunks: List[Chunk] = []
    total_chunks_size = 0
    for chunk in chunks:
        if not chunk or not chunk.content:
            continue
        chunk_size = len(chunk.content)
        if chunk_size < 1:
            continue

        if total_chunks_size + chunk_size >= MAX_CHUNK_SIZE:
            if total_chunks_size > MAX_CHUNK_SIZE:
                print(f"Created a chunk of size {total_chunks_size}")

            if len(temporary_chunks) > 0:
                final_chunks.append(self.__merge_chunks(temporary_chunks))
                while total_chunks_size > MAX_CHUNK_OVERLAP or (
                    total_chunks_size + chunk_size > MAX_CHUNK_SIZE
                    and total_chunks_size > 0
                ):
                    total_chunks_size -= len(temporary_chunks[0].content)
                    temporary_chunks.pop(0)

        temporary_chunks.append(chunk)
        total_chunks_size += chunk_size

    if len(temporary_chunks) > 0:
        final_chunks.append(self.__merge_chunks(temporary_chunks))

    return final_chunks