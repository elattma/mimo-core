CREATE CONSTRAINT document_uniqueness IF NOT EXISTS
FOR (d:Document)
REQUIRE (d.id, d.integration, d.owner) IS NODE KEY;

CREATE CONSTRAINT document_timestamp_existence IF NOT EXISTS
FOR (d:Document)
REQUIRE (d.timestamp) IS NOT NULL;

CREATE CONSTRAINT chunk_uniqueness IF NOT EXISTS
FOR (c:Chunk)
REQUIRE (c.id, c.owner) IS NODE KEY;

CREATE CONSTRAINT chunk_content_existence IF NOT EXISTS
FOR (c:Chunk)
REQUIRE (c.content) IS NOT NULL;

CREATE CONSTRAINT chunk_height_existence IF NOT EXISTS
FOR (c:Chunk)
REQUIRE (c.height) IS NOT NULL;

CREATE CONSTRAINT chunk_timestamp_existence IF NOT EXISTS
FOR (c:Chunk)
REQUIRE (c.timestamp) IS NOT NULL;

CREATE CONSTRAINT entity_uniqueness IF NOT EXISTS
FOR (e:Entity)
REQUIRE (e.id, e.type, e.owner) IS NODE KEY;

CREATE CONSTRAINT predicate_id_existence IF NOT EXISTS
FOR ()-[p:Predicate]-()
REQUIRE (p.id) IS NOT NULL;

CREATE CONSTRAINT predicate_text_existence IF NOT EXISTS
FOR ()-[p:Predicate]-()
REQUIRE (p.text) IS NOT NULL;

CREATE CONSTRAINT predicate_document_existence IF NOT EXISTS
FOR ()-[p:Predicate]-()
REQUIRE (p.document) IS NOT NULL; 

CREATE CONSTRAINT predicate_chunk_existence IF NOT EXISTS
FOR ()-[p:Predicate]-()
REQUIRE (p.chunk) IS NOT NULL;