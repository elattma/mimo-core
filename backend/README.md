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

CREATE CONSTRAINT name_uniqueness IF NOT EXISTS
FOR (n:Name)
REQUIRE (n.id, n.owner) IS NODE KEY;

CREATE RANGE INDEX name_value_index IF NOT EXISTS
FOR (n:Name)
ON (n.value, n.owner);
