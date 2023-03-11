CREATE CONSTRAINT document_uniqueness IF NOT EXISTS
FOR (d:Document)
REQUIRE (d.id, d.integration, d.user) IS NODE KEY;

CREATE CONSTRAINT document_timestamp_existence IF NOT EXISTS
FOR (d:Document)
REQUIRE (d.timestamp) IS NOT NULL;

CREATE CONSTRAINT chunk_uniqueness IF NOT EXISTS
FOR (c:Chunk)
REQUIRE (c.id, c.user) IS NODE KEY;

CREATE CONSTRAINT chunk_content_existence IF NOT EXISTS
FOR (c:Chunk)
REQUIRE (c.content) IS NOT NULL;

CREATE CONSTRAINT chunk_type_existence IF NOT EXISTS
FOR (c:Chunk)
REQUIRE (c.type) IS NOT NULL;

CREATE CONSTRAINT chunk_timestamp_existence IF NOT EXISTS
FOR (c:Chunk)
REQUIRE (c.timestamp) IS NOT NULL;

CREATE CONSTRAINT propernoun_uniqueness IF NOT EXISTS
FOR (p:ProperNoun)
REQUIRE (p.id, p.user) IS NODE KEY;

CREATE CONSTRAINT propernoun_type_existence IF NOT EXISTS
FOR (p:ProperNoun)
REQUIRE (p.type) IS NOT NULL;

CREATE CONSTRAINT propernoun_timestamp_existence IF NOT EXISTS
FOR (p:ProperNoun)
REQUIRE (p.timestamp) IS NOT NULL;