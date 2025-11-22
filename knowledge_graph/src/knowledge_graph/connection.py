"""Neo4j database connection management"""

from neo4j import GraphDatabase
import os


class Neo4jConnection:
    """Manages Neo4j database connection and queries"""

    def __init__(self):
        """Initialize Neo4j connection with environment variables"""
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")

        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            print(f"✓ Connected to Neo4j at {self.uri}")
        except Exception as e:
            print(f"✗ Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()
            print("✓ Disconnected from Neo4j")

    def query(self, cypher: str, params: dict = None):
        """
        Execute a Cypher query and return results

        Args:
            cypher: Cypher query string
            params: Query parameters

        Returns:
            List of dictionaries containing query results
        """
        try:
            with self.driver.session() as session:
                result = session.run(cypher, params or {})
                return [record.data() for record in result]
        except Exception as e:
            print(f"Query error: {e}")
            print(f"Cypher: {cypher}")
            raise

    def execute(self, cypher: str, params: dict = None):
        """
        Execute a Cypher write query (no return)

        Args:
            cypher: Cypher query string
            params: Query parameters
        """
        try:
            with self.driver.session() as session:
                session.run(cypher, params or {})
        except Exception as e:
            print(f"Execute error: {e}")
            print(f"Cypher: {cypher}")
            raise

    def test_connection(self):
        """Test if the connection is working"""
        try:
            result = self.query("RETURN 1 AS test")
            return result[0]["test"] == 1 if result else False
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
