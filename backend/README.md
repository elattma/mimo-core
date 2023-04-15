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

Decision Tree 4/15/2023:

1. if pages are specified
   1a. query(relevant, blocks, page_ids) and return
2. generate query and populate request
   2a. call llm with prompt to generate query components
   2a1. if call fails, then print error and return empty query
3. search or relevant?
   3a. if search then call graph with query
   3b if relevant
   3a1. if page participants then relevant + names
   3a2. if no page participants then relevant
4. Apply return filters
5. Weave context basket and minify if max_tokens is given

decisions to change:

1. instead of relevant 1 time with list of blocks, each block is a separate call?

waterfall fallback:

1.
