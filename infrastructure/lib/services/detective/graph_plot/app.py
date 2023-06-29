import logging
import os
import sys
import traceback
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Set

from algos.classifier import Classifier
from algos.embedder import Embedder
from algos.entity_extractor import EntityExtractor
from algos.normalizer import Normalizer
from dstruct.base import DStruct
from dstruct.graphdb import GraphDB
from dstruct.model import Block, Entity
from dstruct.vectordb import VectorDB
from external.neo4j_ import Neo4j
from external.openai_ import OpenAI
from external.pinecone_ import Pinecone
from lake.s3 import S3Lake
from store.params import SSM

_logger = logging.getLogger('GraphPlot')
logging.basicConfig(level=logging.INFO)

_arg_parser: ArgumentParser = ArgumentParser()
_arg_parser.add_argument('--integration', type=str, required=True)
_arg_parser.add_argument('--connection', type=str, required=True)
_arg_parser.add_argument('--library', type=str, required=True)

def main():
    global _arg_parser, _logger

    lake_bucket_name = os.getenv('LAKE_BUCKET_NAME')
    app_secrets_path = os.getenv('APP_SECRETS_PATH')
    neo4j_uri = os.getenv('NEO4J_URI')
    log_level = os.getenv('LOG_LEVEL')
    log_level = logging.getLevelName(log_level) if log_level else logging.DEBUG
    if not (lake_bucket_name and app_secrets_path and neo4j_uri and log_level):
        raise Exception(f'[main] missing env vars! lake_bucket_name: {lake_bucket_name}, app_secrets_path: {app_secrets_path}, neo4j_uri: {neo4j_uri}')
    
    _logger.setLevel(log_level)
    args = _arg_parser.parse_args()
    args = vars(args)
    integration = args.get('integration', None)
    connection = args.get('connection', None)
    library = args.get('library', None)
    if not (integration and connection and library):
        raise Exception(f'[main] missing args! integration: {integration}, connection: {connection}, library: {library}')
    
    secrets = SSM().load_params(app_secrets_path)
    openai_api_key = secrets.get('openai_api_key', None)
    pinecone_api_key = secrets.get('pinecone_api_key', None)
    neo4j_user = secrets.get('neo4j_user', None)
    neo4j_password = secrets.get('neo4j_password', None)
    if not (openai_api_key and pinecone_api_key and neo4j_user and neo4j_password):
        raise Exception('[main] missing secrets!')

    neo4j = Neo4j(uri=neo4j_uri, user=neo4j_user, password=neo4j_password, log_level=log_level)
    graphdb = GraphDB(db=neo4j)
    pinecone = Pinecone(api_key=pinecone_api_key, environment='us-east1-gcp', index_name='beta', log_level=log_level)
    vectordb = VectorDB(db=pinecone)
    dstruct = DStruct(graphdb=graphdb, vectordb=vectordb, library=library, log_level=log_level)

    llm = OpenAI(api_key=openai_api_key, log_level=log_level)
    classifier = Classifier(log_level=log_level)
    normalizer = Normalizer(max_chunk_len=1000, chunk_overlap=100, log_level=log_level)
    entity_extractor = EntityExtractor(llm=llm, log_level=log_level)
    embedder = Embedder(llm=llm, log_level=log_level)
    
    lake = S3Lake(lake_bucket_name, prefix=f'v1/{library}/{connection}/', log_level=log_level)
    tables = lake.get_tables()
    max_sequential_failures = 200

    for table in tables:
        label = classifier.get_normalized_label(table)
        if not label:
            continue

        _logger.info(f'[main] table: {table}, label: {label}')
        for block_key in lake.block_iterator(table):
            block_dicts = lake.get_block_csv(block_key)
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(
                    ingest_block,
                    dstruct=dstruct,
                    classifier=classifier,
                    normalizer=normalizer,
                    entity_extractor=entity_extractor,
                    embedder=embedder,
                    label=label,
                    integration=integration,
                    connection=connection,
                    block_dict=block_dict
                ) for block_dict in block_dicts]

            for future in as_completed(futures):
                result = future.result()
                if not result:
                    max_sequential_failures -= 1
                    if max_sequential_failures <= 0:
                        dstruct.clean_adjacent_blocks(connection=connection)
                        neo4j.close()
                        raise Exception(f'[main] max_sequential_failures reached!')
                else:
                    max_sequential_failures = 200
                _logger.info(f'[main] result: {result}')

    # TODO: for each root block, find all adjacent blocks. for each cluster of data summarize and embed into the vector db
    dstruct.clean_adjacent_blocks(connection=connection)
    neo4j.close()

def ingest_block(dstruct: DStruct,
                 classifier: Classifier,
                 normalizer: Normalizer,
                 entity_extractor: EntityExtractor,
                 embedder: Embedder,
                 label: str,
                 integration: str,
                 connection: str,
                 block_dict: Dict[str, Any]) -> bool:
    global _logger
    try:
        block_id = classifier.find_id(raw_dict=block_dict, label=label)
        if not block_id:
            _logger.error(f'[ingest_block] error invalid block_id for block: {block_dict}')
            return False
        normalizer.sanitize(block_dict)
        last_updated_timestamp = normalizer.find_last_updated_ts(block_dict)
        dstruct_block = Block(
            id=block_id,
            label=label,
            integration=integration,
            connection=connection,
            properties=None,
            last_updated_timestamp=last_updated_timestamp,
            embedding=None
        )
        normalizer.with_properties(dstruct_block, block_dict)
        embedder.block_with_embeddings(dstruct_block)
        entities: List[Entity] = []
        entity_extractor.with_defined_entities(dictionary=block_dict, entities=entities)
        entity_extractor.with_llm_reasoned_entities(block=dstruct_block, entities=entities)
        entity_extractor.deduplicate(entities)

        adjacent_block_ids: Set[str] = set()
        for entity in entities:
            # hacky way to find adjacent blocks, but it works generally.
            # perhaps associate identifiables with their field?
            # TODO: find a better way to do this..
            if entity.identifiables and len(entity.identifiables) == 1:
                adjacent_block_ids.add(entity.identifiables.pop())

        _logger.info(f'[ingest_block] merging block: {block_id}, entities: {entities}, adjacent_block_ids: {adjacent_block_ids}')
        dstruct.merge(block=dstruct_block, entities=entities, adjacent_block_ids=adjacent_block_ids)
        return True
    except Exception as e:
        _logger.error(f'[ingest_block] error: {str(e)}')
        _logger.error(traceback.format_exc())
        return False

if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        _logger.debug(f'error: {str(e)}')
        _logger.debug(traceback.format_exc())
        sys.exit(1)