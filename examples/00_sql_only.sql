-- ============================================================================
-- SlayDB: Pure SQL Example
-- ============================================================================
-- This example shows how to use SlayDB with just SQL (no Python required).
-- Works with any language that supports SQLite: Node.js, Go, Rust, Java, etc.
-- ============================================================================

-- Load the SlayDB extensions
.load extensions/libgraph
.load extensions/vector

-- Enable column headers and formatting
.headers on
.mode column

-- ============================================================================
-- 1. CREATE GRAPH NODES
-- ============================================================================

-- Initialize the graph
CREATE VIRTUAL TABLE IF NOT EXISTS graph USING graph();

-- Add some documents
INSERT INTO graph_nodes (id, labels, properties) VALUES
  ('doc1', '["Document"]', '{"title": "Introduction to LLMs", "topic": "AI"}'),
  ('doc2', '["Document"]', '{"title": "Building RAG Systems", "topic": "AI"}'),
  ('doc3', '["Document"]', '{"title": "SQLite Performance", "topic": "Database"}');

-- Add some authors
INSERT INTO graph_nodes (id, labels, properties) VALUES
  ('alice', '["Person"]', '{"name": "Alice", "role": "Researcher"}'),
  ('bob', '["Person"]', '{"name": "Bob", "role": "Engineer"}');

SELECT '✓ Created 5 nodes' AS status;

-- ============================================================================
-- 2. CREATE RELATIONSHIPS
-- ============================================================================

-- Link documents to authors
INSERT INTO graph_edges (source, target, edge_type, properties) VALUES
  ('alice', 'doc1', 'AUTHORED', '{"year": 2024}'),
  ('alice', 'doc2', 'AUTHORED', '{"year": 2024}'),
  ('bob', 'doc3', 'AUTHORED', '{"year": 2023}');

-- Link related documents
INSERT INTO graph_edges (source, target, edge_type, properties) VALUES
  ('doc2', 'doc1', 'REFERENCES', '{"context": "builds on concepts"}');

SELECT '✓ Created 4 relationships' AS status;

-- ============================================================================
-- 3. QUERY WITH CYPHER (Graph Pattern Matching)
-- ============================================================================

SELECT '';
SELECT '=== Finding all documents with Cypher ===' AS query;
SELECT cypher_execute('MATCH (d:Document) RETURN d') AS result;

SELECT '';
SELECT '=== Finding who authored what ===' AS query;
SELECT cypher_execute('
  MATCH (p:Person)-[:AUTHORED]->(d:Document)
  RETURN p, d
') AS result;

-- ============================================================================
-- 4. QUERY WITH SQL (Maximum Flexibility)
-- ============================================================================

SELECT '';
SELECT '=== Documents by topic (using SQL) ===' AS query;
SELECT
  id,
  json_extract(properties, '$.title') AS title,
  json_extract(properties, '$.topic') AS topic
FROM graph_nodes
WHERE json_extract(labels, '$[0]') = 'Document'
ORDER BY topic;

SELECT '';
SELECT '=== Authors and their publication count ===' AS query;
SELECT
  n.id AS author,
  json_extract(n.properties, '$.name') AS name,
  COUNT(e.target) AS num_publications
FROM graph_nodes n
JOIN graph_edges e ON n.id = e.source
WHERE e.edge_type = 'AUTHORED'
GROUP BY n.id, name
ORDER BY num_publications DESC;

-- ============================================================================
-- 5. VECTOR SEARCH (Semantic Similarity)
-- ============================================================================

-- Create vector embeddings table
CREATE VIRTUAL TABLE IF NOT EXISTS doc_embeddings USING vector(
  embedding float[384],
  node_id TEXT
);

-- Note: In production, you'd generate embeddings using a model
-- For this example, we'll use placeholder vectors
-- (In Python API, this is done automatically with sentence-transformers)

SELECT '';
SELECT '✓ Vector search setup (add embeddings via your app)' AS status;

-- ============================================================================
-- 6. GRAPH ANALYTICS
-- ============================================================================

SELECT '';
SELECT '=== Graph Statistics ===' AS query;
SELECT
  (SELECT COUNT(*) FROM graph_nodes) AS total_nodes,
  (SELECT COUNT(*) FROM graph_edges) AS total_edges,
  (SELECT COUNT(DISTINCT edge_type) FROM graph_edges) AS unique_edge_types;

SELECT '';
SELECT '=== Most Connected Nodes ===' AS query;
SELECT
  n.id,
  json_extract(n.properties, '$.name') AS name,
  COUNT(e.source) AS outgoing_edges
FROM graph_nodes n
LEFT JOIN graph_edges e ON n.id = e.source
GROUP BY n.id
ORDER BY outgoing_edges DESC;

-- ============================================================================
-- THAT'S IT!
-- ============================================================================

SELECT '';
SELECT '🔥 SlayDB works with pure SQL!' AS message;
SELECT 'Use this from Python, Node.js, Go, Rust, or any language.' AS tip;
