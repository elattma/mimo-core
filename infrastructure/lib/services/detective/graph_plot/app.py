import os
import sys
import traceback
from argparse import ArgumentParser

from algos.classifier import Classifier
from algos.embedder import Embedder
from algos.entity_extractor import EntityExtractor
from algos.normalizer import Normalizer
from algos.relation_extractor import RelationExtractor
from dstruct.base import DStruct
from dstruct.graphdb import GraphDB
from dstruct.model import Block
from dstruct.vectordb import VectorDB
from external.neo4j_ import Neo4j
from external.openai_ import OpenAI
from external.pinecone_ import Pinecone
from lake.s3 import S3Lake
from store.params import SSM

_arg_parser: ArgumentParser = ArgumentParser()
_arg_parser.add_argument('--integration', type=str, required=True)
_arg_parser.add_argument('--connection', type=str, required=True)
_arg_parser.add_argument('--library', type=str, required=True)

def main():
    lake_bucket_name = os.getenv('LAKE_BUCKET_NAME')
    app_secrets_path = os.getenv('APP_SECRETS_PATH')
    neo4j_uri = os.getenv('NEO4J_URI')
    if not (lake_bucket_name and app_secrets_path and neo4j_uri):
        raise Exception(f'[main] missing env vars! lake_bucket_name: {lake_bucket_name}, app_secrets_path: {app_secrets_path}, neo4j_uri: {neo4j_uri}')
    
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

    neo4j = Neo4j(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)
    graphdb = GraphDB(db=neo4j)
    pinecone = Pinecone(api_key=pinecone_api_key, environment='us-east1-gcp', index_name='beta')
    vectordb = VectorDB(db=pinecone)
    dstruct = DStruct(graphdb=graphdb, vectordb=vectordb, library=library)

    llm = OpenAI(openai_api_key)
    classifier = Classifier()
    normalizer = Normalizer()
    entity_extractor = EntityExtractor()
    relation_extractor = RelationExtractor()
    embedder = Embedder(llm)
    
    # TODO: remove test prefix
    lake = S3Lake(lake_bucket_name, prefix=f'test/{library}/{connection}/')
    tables = lake.get_tables()

    for table in tables:
        label = classifier.get_normalized_label(table)
        print(f'[main] table: {table}, label: {label}')
        for block_key in lake.block_iterator(table):
            block_dicts = lake.get_block_csv(block_key)
            for block_dict in block_dicts:
                block_id = classifier.find_id(block_dict)
                if not block_id:
                    print(f'[main] invalid block_id for block: {block_dict}')
                    continue
                print(f'[main] block_id: {block_id}')
                normalizer.sanitize(block_dict)
                last_updated_timestamp = normalizer.find_last_updated_timestamp(block_dict)
                dstruct_block = Block(
                    id=block_id,
                    label=label,
                    integration=integration,
                    properties=None,
                    last_updated_timestamp=last_updated_timestamp,
                    embedding=None
                )
                normalizer.with_properties(dstruct_block, block_dict)
                print(f'[main] block: {dstruct_block}')
                print(f'[main] block_dict: {block_dict}')
                embedder.block_with_embeddings(dstruct_block)
                entities = entity_extractor.find_entities(block_dict)
                inferrable_entities = entity_extractor.find_inferrable_entities(block_dict)
                adjacent_block_ids = relation_extractor.find_adjacent_blocks(block_dict)

                succeeded = dstruct.merge(
                    block=dstruct_block,
                    entities=entities,
                    adjacent_block_ids=adjacent_block_ids,
                    inferrable_entity_values=inferrable_entities
                )
                print(f'[main] merge succeeded: {succeeded}')
                if not succeeded:
                    raise Exception('failed to merge block', block_dict)
                neo4j.close()
                return

    # TODO: for each root block, find all adjacent blocks
    # for each cluster of data
        # summarize and embed into the vector db


if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f'error: {str(e)}')
        print(traceback.format_exc())
        sys.exit(1)