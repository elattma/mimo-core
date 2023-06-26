from neo4j import GraphDatabase


class Neo4j:
    def __init__(self, uri: str, user: str, password: str):
        print(f'[Neo4j.__init__] starting')
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        with self.driver:
            self.driver.verify_connectivity()
        print(f'[Neo4j.__init__] completed')

    def write(self, query: str, **kwargs):
        with self.driver.session(database='neo4j') as session:
            result = session.execute_write(self._call, query, **kwargs)
            return result
        
    def read(self, query: str, **kwargs):
        with self.driver.session(database='neo4j') as session:
            result = session.execute_read(self._call, query, **kwargs)
            return result

    @staticmethod
    def _call(tx, query, **kwargs):
        print(f'[Neo4j._call] query: {query}, kwargs: {kwargs}')
        if not query:
            raise ValueError('query must not be empty')

        result = tx.run(query, **kwargs)
        print(f'[Neo4j._call] result: {str(result)}')
        return list(result)

    def close(self):
        print('[Neo4j.close] closing driver')
        self.driver.close()
    