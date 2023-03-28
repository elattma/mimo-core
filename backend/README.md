To configure the Neo4J DB, run the following commands:

CREATE CONSTRAINT document_uniqueness IF NOT EXISTS
FOR (d:Document)
REQUIRE (d.id, d.integration, d.owner) IS NODE KEY;

CREATE CONSTRAINT document_timestamp_existence IF NOT EXISTS
FOR (d:Document)
REQUIRE (d.timestamp) IS NOT NULL;

CREATE CONSTRAINT block_uniqueness IF NOT EXISTS
FOR (b:Block)
REQUIRE (b.id, b.owner) IS NODE KEY;

CREATE CONSTRAINT block_label_existence IF NOT EXISTS
FOR (b:Block)
REQUIRE (b.label) IS NOT NULL;

CREATE CONSTRAINT block_content_existence IF NOT EXISTS
FOR (b:Block)
REQUIRE (b.content) IS NOT NULL;

CREATE CONSTRAINT block_timestamp_existence IF NOT EXISTS
FOR (b:Block)
REQUIRE (b.timestamp) IS NOT NULL;

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
