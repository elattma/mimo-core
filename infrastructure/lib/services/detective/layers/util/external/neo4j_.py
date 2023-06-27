from logging import getLogger

from neo4j import GraphDatabase

_logger = getLogger('Neo4j')

class Neo4j:
    def __init__(self, uri: str, user: str, password: str, log_level: int):
        _logger.setLevel(log_level)
        _logger.info('[__init__] starting')
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        with self.driver:
            self.driver.verify_connectivity()
        _logger.info('[__init__] completed')

    def write(self, query: str, **kwargs):
        with self.driver.session(database='neo4j') as session:
            _logger.debug(f'[write] query: {query}, kwargs: {kwargs}')
            result = session.execute_write(self._call, query, **kwargs)
            _logger.debug(f'[write] result: {str(result)}')
            return result
        
    def read(self, query: str, **kwargs):
        with self.driver.session(database='neo4j') as session:
            result = session.execute_read(self._call, query, **kwargs)
            return result

    @staticmethod
    def _call(tx, query, **kwargs):
        if not query:
            raise ValueError('query must not be empty')

        result = tx.run(query, **kwargs)
        return list(result)

    def close(self):
        _logger.debug('[close] closing driver')
        self.driver.close()
    