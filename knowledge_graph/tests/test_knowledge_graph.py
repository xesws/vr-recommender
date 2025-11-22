"""Unit tests for knowledge graph module"""

import unittest
import json
import os
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from knowledge_graph.src.knowledge_graph.connection import Neo4jConnection
from knowledge_graph.src.knowledge_graph.schema import KnowledgeGraphSchema
from knowledge_graph.src.knowledge_graph.nodes import NodeCreator
from knowledge_graph.src.knowledge_graph.relationships import RelationshipCreator


class TestNeo4jConnection(unittest.TestCase):
    """Test Neo4j connection management"""

    @patch('knowledge_graph.src.knowledge_graph.connection.GraphDatabase')
    def test_connection_init(self, mock_graph_db):
        """Test connection initialization"""
        # Mock driver
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver

        # Create connection
        conn = Neo4jConnection()

        # Verify driver creation
        mock_graph_db.driver.assert_called_once()
        self.assertIsNotNone(conn.driver)

    def test_connection_close(self):
        """Test connection closing"""
        with patch('knowledge_graph.src.knowledge_graph.connection.GraphDatabase') as mock_graph_db:
            mock_driver = MagicMock()
            mock_graph_db.driver.return_value = mock_driver

            conn = Neo4jConnection()
            conn.close()

            mock_driver.close.assert_called_once()

    def test_query_execution(self):
        """Test query execution"""
        with patch('knowledge_graph.src.knowledge_graph.connection.GraphDatabase') as mock_graph_db:
            mock_driver = MagicMock()
            mock_session = MagicMock()
            mock_result = MagicMock()

            mock_session.run.return_value = mock_result
            mock_result.__iter__ = lambda self: iter([Mock(data=lambda: {'test': 1})])
            mock_driver.session.return_value = mock_session
            mock_graph_db.driver.return_value = mock_driver

            conn = Neo4jConnection()
            result = conn.query("RETURN 1 AS test")

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['test'], 1)


class TestKnowledgeGraphSchema(unittest.TestCase):
    """Test schema initialization"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_conn = Mock()
        self.schema = KnowledgeGraphSchema(self.mock_conn)

    def test_init_constraints(self):
        """Test constraint initialization"""
        self.schema.init_constraints()

        # Verify all constraints were executed
        self.assertEqual(self.mock_conn.execute.call_count, 3)

    def test_init_indexes(self):
        """Test index initialization"""
        self.schema.init_indexes()

        # Verify all indexes were executed
        self.assertEqual(self.mock_conn.execute.call_count, 4)

    def test_clear_database(self):
        """Test database clearing"""
        self.schema.clear_database()

        # Verify delete query was executed
        self.mock_conn.execute.assert_called_once_with("MATCH (n) DETACH DELETE n")


class TestNodeCreator(unittest.TestCase):
    """Test node creation"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_conn = Mock()
        self.nodes = NodeCreator(self.mock_conn)

        # Create test data
        self.test_courses = [
            {
                "course_id": "test_1",
                "title": "Test Course",
                "department": "Test Dept",
                "description": "Test Description",
                "units": 12
            }
        ]

        self.test_apps = [
            {
                "app_id": "test_app_1",
                "name": "Test VR App",
                "category": "Education",
                "description": "Test Description",
                "rating": 4.5,
                "price": "Free",
                "features": ["feature1", "feature2"]
            }
        ]

        self.test_skills = [
            {
                "name": "Python Programming",
                "category": "technical",
                "aliases": ["Python", "Py"],
                "source_count": 5,
                "weight": 0.9
            }
        ]

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('json.load')
    def test_create_courses(self, mock_json_load, mock_open):
        """Test course node creation"""
        mock_json_load.return_value = self.test_courses

        self.nodes.create_courses("test_path.json")

        # Verify execute was called
        self.assertTrue(self.mock_conn.execute.called)

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('json.load')
    def test_create_apps(self, mock_json_load, mock_open):
        """Test VR app node creation"""
        mock_json_load.return_value = self.test_apps

        self.nodes.create_apps("test_path.json")

        # Verify execute was called
        self.assertTrue(self.mock_conn.execute.called)

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('json.load')
    def test_create_skills(self, mock_json_load, mock_open):
        """Test skill node creation"""
        mock_json_load.return_value = self.test_skills

        self.nodes.create_skills("test_path.json")

        # Verify execute was called
        self.assertTrue(self.mock_conn.execute.called)


class TestRelationshipCreator(unittest.TestCase):
    """Test relationship creation"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_conn = Mock()
        self.relations = RelationshipCreator(self.mock_conn)

        # Create test mappings
        self.test_course_skills = [
            {
                "source_id": "test_1",
                "source_type": "course",
                "skill_name": "Python Programming",
                "weight": 0.9
            }
        ]

        self.test_app_skills = [
            {
                "source_id": "test_app_1",
                "source_type": "app",
                "skill_name": "Python Programming",
                "weight": 0.8
            }
        ]

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('json.load')
    def test_create_course_skill_relations(self, mock_json_load, mock_open):
        """Test TEACHES relationship creation"""
        mock_json_load.return_value = self.test_course_skills

        self.relations.create_course_skill_relations("test_path.json")

        # Verify execute was called
        self.assertTrue(self.mock_conn.execute.called)

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('json.load')
    def test_create_app_skill_relations(self, mock_json_load, mock_open):
        """Test DEVELOPS relationship creation"""
        mock_json_load.return_value = self.test_app_skills

        self.relations.create_app_skill_relations("test_path.json")

        # Verify execute was called
        self.assertTrue(self.mock_conn.execute.called)

    def test_compute_recommendations(self):
        """Test recommendation computation"""
        # Mock the query for counting
        self.mock_conn.query.return_value = [{"count": 5}]

        self.relations.compute_recommendations()

        # Verify execute was called
        self.assertTrue(self.mock_conn.execute.called)


class TestKnowledgeGraphBuilder(unittest.TestCase):
    """Test knowledge graph builder integration"""

    @patch('knowledge_graph.src.knowledge_graph.builder.Neo4jConnection')
    def test_builder_init(self, mock_conn_class):
        """Test builder initialization"""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn

        builder = KnowledgeGraphBuilder()

        self.assertIsNotNone(builder.conn)
        self.assertIsNotNone(builder.schema)
        self.assertIsNotNone(builder.nodes)
        self.assertIsNotNone(builder.relations)

    @patch('knowledge_graph.src.knowledge_graph.builder.Neo4jConnection')
    @patch('knowledge_graph.src.knowledge_graph.builder.KnowledgeGraphSchema')
    @patch('knowledge_graph.src.knowledge_graph.builder.NodeCreator')
    @patch('knowledge_graph.src.knowledge_graph.builder.RelationshipCreator')
    def test_build(self, mock_rel_class, mock_node_class, mock_schema_class, mock_conn_class):
        """Test complete build process"""
        # Mock all components
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        mock_schema = MagicMock()
        mock_schema_class.return_value = mock_schema
        mock_nodes = MagicMock()
        mock_node_class.return_value = mock_nodes
        mock_relations = MagicMock()
        mock_rel_class.return_value = mock_relations

        builder = KnowledgeGraphBuilder()
        builder.build(data_dir="test_data", clear=False)

        # Verify all steps were called
        mock_schema.init_constraints.assert_called_once()
        mock_schema.init_indexes.assert_called_once()
        mock_nodes.create_courses.assert_called_once()
        mock_nodes.create_apps.assert_called_once()
        mock_nodes.create_skills.assert_called_once()
        mock_relations.create_course_skill_relations.assert_called_once()
        mock_relations.create_app_skill_relations.assert_called_once()
        mock_relations.compute_recommendations.assert_called_once()


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
