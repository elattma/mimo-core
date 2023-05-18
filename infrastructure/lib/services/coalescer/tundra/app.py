from fetcher.base import Fetcher, Filter


def checkpoint():
    pass

def fetch(integration: str, access_token: str):
    fetcher: Fetcher = Fetcher.create(integration, access_token)
    # fetch
    # batch write to s3
    # checkpoint
    pass

def paginate():
    # get from s3
    # joins, create blocks and pages
    # checkpoint
    pass

def load(library: str):
    # get from s3
    # load into pinecone, neo4j
    # checkpoint
    pass

def main():
    pass

    # remember user
    # remember connection 
    # remmeber to checkpoint
    # need filter params?

print('here! hello world!')
