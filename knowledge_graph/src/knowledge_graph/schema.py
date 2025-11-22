"""Knowledge graph schema initialization (constraints and indexes)"""

class KnowledgeGraphSchema:
    """Manages Neo4j schema constraints and indexes"""

    def __init__(self, connection):
        """
        Initialize schema manager

        Args:
            connection: Neo4jConnection instance
        """
        self.conn = connection

    def init_constraints(self):
        """Create unique constraints for primary keys"""
        constraints = [
            "CREATE CONSTRAINT course_id IF NOT EXISTS FOR (c:Course) REQUIRE c.course_id IS UNIQUE",
            "CREATE CONSTRAINT app_id IF NOT EXISTS FOR (a:VRApp) REQUIRE a.app_id IS UNIQUE",
            "CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE",
        ]

        print("\n[Schema] Creating constraints...")
        for constraint in constraints:
            try:
                self.conn.execute(constraint)
                print(f"  ✓ Constraint created")
            except Exception as e:
                # Constraint may already exist
                print(f"  • Constraint: {constraint.split('FOR')[1].split(')')[0].strip()}")

        print("✓ Constraints initialized")

    def init_indexes(self):
        """Create indexes for better query performance"""
        indexes = [
            "CREATE INDEX course_department IF NOT EXISTS FOR (c:Course) ON (c.department)",
            "CREATE INDEX app_category IF NOT EXISTS FOR (a:VRApp) ON (a.category)",
            "CREATE INDEX skill_category IF NOT EXISTS FOR (s:Skill) ON (s.category)",
            "CREATE INDEX skill_source_count IF NOT EXISTS FOR (s:Skill) ON (s.source_count)",
        ]

        print("\n[Schema] Creating indexes...")
        for index in indexes:
            try:
                self.conn.execute(index)
                print(f"  ✓ Index created")
            except Exception as e:
                # Index may already exist
                print(f"  • Index: {index.split('FOR')[1].split(')')[0].strip()}")

        print("✓ Indexes initialized")

    def clear_database(self):
        """Clear all data from the database (USE WITH CAUTION)"""
        print("\n[WARN] Clearing entire database...")
        try:
            self.conn.execute("MATCH (n) DETACH DELETE n")
            print("✓ Database cleared successfully")
        except Exception as e:
            print(f"✗ Failed to clear database: {e}")
            raise

    def drop_all_constraints_and_indexes(self):
        """Drop all constraints and indexes (for cleanup)"""
        print("\n[Schema] Dropping all constraints and indexes...")
        try:
            self.conn.execute("CALL apoc.schema.drop() YIELD name RETURN name")
            print("✓ All constraints and indexes dropped")
        except Exception as e:
            print(f"Note: apoc.schema.drop() not available: {e}")
            # Try manual drop
            self.conn.execute("DROP CONSTRAINT * IF EXISTS")
            self.conn.execute("DROP INDEX * IF EXISTS")
            print("✓ Constraints and indexes dropped (manual)")

    def show_schema(self):
        """Display current schema information"""
        print("\n[Schema] Current constraints:")
        try:
            result = self.conn.query("SHOW CONSTRAINTS")
            for record in result:
                print(f"  • {record.get('name', 'N/A')}: {record.get('type', 'N/A')}")
        except Exception as e:
            print(f"  Could not retrieve constraints: {e}")

        print("\n[Schema] Current indexes:")
        try:
            result = self.conn.query("SHOW INDEXES")
            for record in result:
                print(f"  • {record.get('name', 'N/A')}: {record.get('type', 'N/A')}")
        except Exception as e:
            print(f"  Could not retrieve indexes: {e}")
