from dataclasses import dataclass
from typing import List

from app.client.neo4j import (Chunk, Consists, Document, Entity, Neo4j,
                              Predicate)
from app.client.open_ai import OpenAI
from app.client.pinecone import Pinecone, Row, RowType
from app.client.spacy import Spacy, Triplet
from ulid import ulid


@dataclass
class IngestInput:
    owner: str
    integration: str
    document_id: str
    chunks: List[str]
    timestamp: int

@dataclass
class IngestResponse:
    succeeded: bool
    integration: str
    timestamp: int

MAX_TREE_CHUNKS_CHILDREN = 10

class Ingestor:
    _spacy: Spacy = None

    def __init__(self, openai: OpenAI, neo4j: Neo4j, pinecone: Pinecone):
        self._openai = openai
        self._neo4j = neo4j
        self._pinecone = pinecone
        if not self._spacy:
            self._spacy = Spacy()

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
                tree_chunks.append(Chunk(
                    id=ulid(),
                    embedding=chunk_embedding,
                    content=chunk,
                    height=height
                ))
            for i in range(0, temp_chunks_len, MAX_TREE_CHUNKS_CHILDREN):
                summary = self._openai.summarize('\n\n'.join(temp_chunks[i:min(i+MAX_TREE_CHUNKS_CHILDREN, temp_chunks_len)]))
                join_chunks.append(summary)
            temp_chunks = join_chunks
            height += 1
        if len(temp_chunks) == 1:
            chunk_embedding = self._openai.embed(chunk)
            tree_chunks.append(Chunk(
                id=ulid(),
                embedding=chunk_embedding,
                content=chunk,
                height=height
            ))
        return tree_chunks

    def _get_document(self, document_id: str, integration: str, chunks: List[Chunk]) -> Document:
        document = Document(
            id=document_id,
            integration=integration,
            consists=[Consists(target=chunk) for chunk in chunks]
        )
        return document

    def _get_triplet_entities(self, document_id: str, chunk_id: str, chunk: str) -> List[Entity]:
        triplets: List[Triplet] = self._spacy.get_triplets(chunk) # TODO: implement

        entities_dict: dict[str, Entity] = {}
        for triplet in triplets:
            triplet_id = ulid()
            triplet_embedding = self._openai.embed(text=f'{triplet.subject} {triplet.predicate} {triplet.object}')

            object_entity = Entity(
                id=triplet.object.text,
                type=triplet.object.type
            )

            predicate = Predicate(
                id=triplet_id,
                embedding=triplet_embedding,
                text=triplet.predicate.text,
                chunk=chunk_id,
                document=document_id,
                target=object_entity
            )

            if triplet.subject not in entities_dict:
                entities_dict[triplet.subject] = Entity(
                    id=triplet.subject.text,
                    type=triplet.subject.type,
                    predicates=[predicate]
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
        succeeded = True
        try:
            document = self._get_document(document_id=input.document_id, integration=input.integration, chunks=self._get_chunks(input.chunks))
            triplet_entities = []
            for chunk in document.consists:
                entities = self._get_triplet_entities(document_id=document.id, chunk_id=chunk.target.id, chunk=chunk.target.content)
                triplet_entities.extend(entities)
            
            triplet_entities = self._squash_triplet_entities(triplet_entities)
            pinecone_response = self._pinecone_write(owner=input.owner, document=document, entities=triplet_entities)
            neo4j_response = self._neo4j_write(owner=input.owner, document=document, entities=triplet_entities, timestamp=input.timestamp)

            print(pinecone_response)
            print(neo4j_response)
        except Exception as e:
            print(e)
            succeeded = False

        return IngestResponse(succeeded=succeeded, integration=input.integration, timestamp=input.timestamp)

    def _pinecone_write(self, owner: str, document: Document, entities: List[Entity]) -> bool:
        rows: List[Row] = []
        for chunk in document.consists:
            chunk_row = Row(
                id=chunk.target.id,
                embedding=chunk.target.embedding,
                owner=owner,
                document_id=document.id,
                type=RowType.CHUNK
            )
            rows.append(chunk_row)
        
        for entity in entities:
            for triplet in entity.predicates:
                triplet_row = Row(
                    id=triplet.id,
                    embedding=triplet.embedding,
                    owner=owner,
                    document_id=triplet.document,
                    type=RowType.TRIPLET
                )
                rows.append(triplet_row)

        return self._pinecone.upsert(rows)
    
    def _neo4j_write(self, entities: List[Entity], documents: List[Document], owner: str, timestamp: int) -> bool:
        return self._neo4j.create_entities(entities=entities, documents=documents, owner=owner, timestamp=timestamp)