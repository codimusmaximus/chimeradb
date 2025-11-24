"""
ChimeraDB Knowledge Graph

Semantic search + graph queries + SQL analytics in one database.
Powered by DuckDB for production-grade performance and reliability.
"""

import duckdb
import json
from typing import List, Dict, Any, Optional, Tuple
import warnings

class KnowledgeGraph:
    """
    A unified database combining:
    - Property graphs (SQL/PGQ standard for graph pattern matching)
    - Vector embeddings (HNSW indexing for semantic search)
    - Full SQL analytics (DuckDB's columnar engine)

    All in a single DuckDB file with zero infrastructure.
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        embedding_model: Optional[str] = "all-MiniLM-L6-v2",
        auto_embed: bool = True
    ):
        """
        Initialize Knowledge Graph with DuckDB backend.

        Args:
            db_path: Path to database file, or ":memory:" for in-memory
            embedding_model: Sentence transformer model name, or None to disable
            auto_embed: Automatically generate embeddings for new nodes
        """
        self.db_path = db_path
        self.auto_embed = auto_embed and (embedding_model is not None)
        self.embedding_model_name = embedding_model
        self.embedder = None
        self.embedding_dim = None

        # Initialize embedding model if requested
        if embedding_model:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedder = SentenceTransformer(embedding_model)
                # Get embedding dimension
                test_emb = self.embedder.encode("test")
                self.embedding_dim = len(test_emb)
            except ImportError:
                warnings.warn(
                    "sentence-transformers not installed. Install with: "
                    "pip install sentence-transformers"
                )
                self.auto_embed = False

        # Connect to DuckDB with HNSW persistence enabled
        config = {}
        if db_path != ":memory:":
            config['hnsw_enable_experimental_persistence'] = 'true'

        self.conn = duckdb.connect(db_path, config=config)

        # Install and load extensions
        self._setup_extensions()

        # Initialize schema
        self._init_schema()

    def _setup_extensions(self):
        """Install and load DuckDB extensions."""
        try:
            self.conn.execute("INSTALL duckpgq FROM community")
            self.conn.execute("LOAD duckpgq")
        except Exception as e:
            warnings.warn(f"Failed to load duckpgq extension: {e}")

        try:
            self.conn.execute("INSTALL vss")
            self.conn.execute("LOAD vss")
        except Exception as e:
            warnings.warn(f"Failed to load vss extension: {e}")

    def _init_schema(self):
        """Initialize database schema with nodes, edges, and property graph."""
        emb_type = f"FLOAT[{self.embedding_dim}]" if self.embedding_dim else "FLOAT[]"

        # Create nodes table
        self.conn.execute(f"""
            CREATE TABLE IF NOT EXISTS nodes (
                id VARCHAR PRIMARY KEY,
                labels VARCHAR,  -- JSON array of labels
                properties JSON,
                embedding {emb_type}
            )
        """)

        # Create edges table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                from_id VARCHAR,
                to_id VARCHAR,
                edge_type VARCHAR,
                properties JSON,
                FOREIGN KEY (from_id) REFERENCES nodes(id),
                FOREIGN KEY (to_id) REFERENCES nodes(id)
            )
        """)

        # Create HNSW index for vector similarity if embeddings enabled
        if self.embedding_dim:
            try:
                self.conn.execute("""
                    CREATE INDEX IF NOT EXISTS nodes_embedding_idx
                    ON nodes USING HNSW (embedding)
                """)
            except Exception:
                pass  # Index might already exist

        # Create property graph
        try:
            self.conn.execute("""
                CREATE OR REPLACE PROPERTY GRAPH knowledge_graph
                VERTEX TABLES (nodes PROPERTIES (id, labels, properties))
                EDGE TABLES (
                    edges
                    SOURCE KEY (from_id) REFERENCES nodes (id)
                    DESTINATION KEY (to_id) REFERENCES nodes (id)
                    PROPERTIES (edge_type, properties)
                )
            """)
        except Exception as e:
            # Property graph might already exist or duckpgq not available
            pass

    def add_entity(
        self,
        entity_id: str,
        properties: Dict[str, Any],
        labels: Optional[List[str]] = None,
        embedding: Optional[List[float]] = None,
        auto_embed: Optional[bool] = None,
        embed_field: str = "text"
    ) -> str:
        """
        Add a node to the graph.

        Args:
            entity_id: Unique identifier for the node
            properties: Dictionary of node properties
            labels: List of labels/types for the node
            embedding: Pre-computed embedding vector
            auto_embed: Override default auto_embed setting
            embed_field: Property field to use for embedding generation

        Returns:
            entity_id
        """
        labels = labels or []
        labels_json = json.dumps(labels)
        properties_json = json.dumps(properties)

        # Generate embedding if requested
        should_embed = (auto_embed if auto_embed is not None else self.auto_embed)
        if should_embed and embedding is None and embed_field in properties:
            text = properties[embed_field]
            if self.embedder and text:
                embedding = self.embedder.encode(text).tolist()

        # Insert or update node
        self.conn.execute("""
            INSERT OR REPLACE INTO nodes (id, labels, properties, embedding)
            VALUES (?, ?, ?::JSON, ?)
        """, [entity_id, labels_json, properties_json, embedding])

        return entity_id

    def add_relationship(
        self,
        from_id: str,
        to_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Add an edge between two nodes.

        Args:
            from_id: Source node ID
            to_id: Target node ID
            relation_type: Type/label of the relationship
            properties: Optional edge properties
        """
        properties = properties or {}
        properties_json = json.dumps(properties)

        self.conn.execute("""
            INSERT INTO edges (from_id, to_id, edge_type, properties)
            VALUES (?, ?, ?, ?::JSON)
        """, [from_id, to_id, relation_type, properties_json])

    def search(
        self,
        query: str,
        top_k: int = 10,
        labels: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search using vector similarity.

        Args:
            query: Search query text
            top_k: Number of results to return
            labels: Optional filter by node labels

        Returns:
            List of matching nodes with similarity scores
        """
        if not self.embedder:
            raise ValueError("No embedding model configured")

        # Generate query embedding
        query_emb = self.embedder.encode(query).tolist()

        # Build label filter
        label_filter = ""
        if labels:
            label_conditions = " OR ".join([f"labels LIKE '%{label}%'" for label in labels])
            label_filter = f"WHERE ({label_conditions})"

        # Search with vector similarity
        results = self.conn.execute(f"""
            SELECT
                id,
                labels,
                properties,
                1.0 - (array_distance(embedding, ?::FLOAT[{self.embedding_dim}]) / 10.0) as similarity
            FROM nodes
            {label_filter}
            ORDER BY array_distance(embedding, ?::FLOAT[{self.embedding_dim}])
            LIMIT ?
        """, [query_emb, query_emb, top_k]).fetchall()

        return [
            {
                "id": row[0],
                "labels": json.loads(row[1]) if row[1] else [],
                "properties": json.loads(row[2]) if row[2] else {},
                "similarity": max(0.0, row[3]) if row[3] else 0.0
            }
            for row in results
        ]

    def traverse(
        self,
        start_id: str,
        relation_type: Optional[str] = None,
        max_depth: int = 3,
        direction: str = "outgoing"
    ) -> List[Dict[str, Any]]:
        """
        Traverse the graph from a starting node.

        Args:
            start_id: Starting node ID
            relation_type: Optional relationship type to follow
            max_depth: Maximum traversal depth
            direction: "outgoing", "incoming", or "both"

        Returns:
            List of reachable nodes with depth info
        """
        # Build CTE based on direction
        if direction == "outgoing":
            join_cond = "c.id = e.from_id"
            next_id = "e.to_id"
        elif direction == "incoming":
            join_cond = "c.id = e.to_id"
            next_id = "e.from_id"
        else:  # both
            join_cond = "(c.id = e.from_id OR c.id = e.to_id)"
            next_id = "CASE WHEN c.id = e.from_id THEN e.to_id ELSE e.from_id END"

        rel_filter = f"AND e.edge_type = '{relation_type}'" if relation_type else ""

        query = f"""
            WITH RECURSIVE traversal(id, depth, path) AS (
                SELECT id, 0, id
                FROM nodes WHERE id = ?
                UNION
                SELECT n.id, c.depth + 1, c.path || ',' || n.id
                FROM traversal c
                JOIN edges e ON {join_cond}
                JOIN nodes n ON n.id = {next_id}
                WHERE c.depth < ? {rel_filter}
                  AND position(',' || n.id || ',' IN ',' || c.path || ',') = 0
            )
            SELECT DISTINCT t.id, t.depth, n.properties
            FROM traversal t
            JOIN nodes n ON t.id = n.id
            WHERE t.depth > 0
            ORDER BY t.depth, t.id
        """

        results = self.conn.execute(query, [start_id, max_depth]).fetchall()

        return [
            {
                "id": row[0],
                "depth": row[1],
                "properties": json.loads(row[2]) if row[2] else {}
            }
            for row in results
        ]

    def query(self, sql: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """
        Execute raw SQL query.

        Args:
            sql: SQL query string
            params: Optional query parameters

        Returns:
            Query results as list of tuples
        """
        if params:
            return self.conn.execute(sql, params).fetchall()
        return self.conn.execute(sql).fetchall()

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by ID.

        Args:
            entity_id: Node ID

        Returns:
            Node data or None if not found
        """
        result = self.conn.execute(
            "SELECT id, labels, properties FROM nodes WHERE id = ?",
            [entity_id]
        ).fetchone()

        if not result:
            return None

        return {
            "id": result[0],
            "labels": json.loads(result[1]) if result[1] else [],
            "properties": json.loads(result[2]) if result[2] else {}
        }

    def commit(self):
        """Commit transaction (no-op for DuckDB which auto-commits)."""
        pass  # DuckDB auto-commits by default

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
