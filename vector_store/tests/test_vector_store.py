"""
Tests for Stage 4 vector store functionality.
"""

import pytest
import json
import os
import sys
import tempfile
import shutil

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from vector_store.src.vector_store.indexer import VectorIndexer


class TestVectorIndexer:
    """Test suite for VectorIndexer."""

    @pytest.fixture
    def sample_skills(self):
        """Sample skills for testing."""
        return [
            {
                "name": "Machine Learning",
                "aliases": ["ML", "Artificial Intelligence"],
                "category": "technical",
                "source_count": 5,
                "weight": 0.95
            },
            {
                "name": "Deep Learning",
                "aliases": ["Neural Networks", "DL"],
                "category": "technical",
                "source_count": 3,
                "weight": 0.9
            },
            {
                "name": "Python Programming",
                "aliases": ["Python", "Py"],
                "category": "technical",
                "source_count": 8,
                "weight": 0.95
            },
            {
                "name": "Public Policy",
                "aliases": ["Policy Analysis"],
                "category": "domain",
                "source_count": 4,
                "weight": 0.85
            },
            {
                "name": "Communication",
                "aliases": ["Interpersonal Skills"],
                "category": "soft",
                "source_count": 6,
                "weight": 0.8
            }
        ]

    @pytest.fixture
    def temp_dir(self):
        """Temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_build_index(self, sample_skills, temp_dir):
        """Test building vector index."""
        skills_file = os.path.join(temp_dir, "skills.json")
        with open(skills_file, 'w') as f:
            json.dump(sample_skills, f)

        indexer = VectorIndexer(
            use_openai=False,
            persist_dir=os.path.join(temp_dir, "chroma")
        )

        indexer.build_index(skills_file, clear_existing=True)

        stats = indexer.get_stats()
        assert stats['total_skills'] == len(sample_skills)

    def test_search(self, sample_skills, temp_dir):
        """Test skill search functionality."""
        skills_file = os.path.join(temp_dir, "skills.json")
        with open(skills_file, 'w') as f:
            json.dump(sample_skills, f)

        indexer = VectorIndexer(
            use_openai=False,
            persist_dir=os.path.join(temp_dir, "chroma")
        )

        indexer.build_index(skills_file)

        # Test ML search
        results = indexer.search("machine learning", top_k=3)

        assert len(results) > 0
        assert results[0][0] in ["Machine Learning", "Deep Learning"]

        # Verify result format
        for name, score, meta in results:
            assert isinstance(name, str)
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0
            assert isinstance(meta, dict)

    def test_search_with_similarity_threshold(self, sample_skills, temp_dir):
        """Test search with similarity threshold."""
        skills_file = os.path.join(temp_dir, "skills.json")
        with open(skills_file, 'w') as f:
            json.dump(sample_skills, f)

        indexer = VectorIndexer(
            use_openai=False,
            persist_dir=os.path.join(temp_dir, "chroma")
        )

        indexer.build_index(skills_file)

        # High threshold should return fewer results
        high_threshold_results = indexer.search(
            "machine learning",
            top_k=10,
            min_similarity=0.7
        )

        assert len(high_threshold_results) <= len(
            indexer.search("machine learning", top_k=10, min_similarity=0.0)
        )

    def test_batch_search(self, sample_skills, temp_dir):
        """Test batch search functionality."""
        skills_file = os.path.join(temp_dir, "skills.json")
        with open(skills_file, 'w') as f:
            json.dump(sample_skills, f)

        indexer = VectorIndexer(
            use_openai=False,
            persist_dir=os.path.join(temp_dir, "chroma")
        )

        indexer.build_index(skills_file)

        queries = ["machine learning", "public policy", "communication"]
        results = indexer.batch_search(queries, top_k=3)

        assert len(results) == len(queries)
        for result in results:
            assert len(result) > 0

    def test_get_skill_info(self, sample_skills, temp_dir):
        """Test retrieving skill information."""
        skills_file = os.path.join(temp_dir, "skills.json")
        with open(skills_file, 'w') as f:
            json.dump(sample_skills, f)

        indexer = VectorIndexer(
            use_openai=False,
            persist_dir=os.path.join(temp_dir, "chroma")
        )

        indexer.build_index(skills_file)

        # Get info for existing skill
        info = indexer.get_skill_info("Machine Learning")
        assert info is not None
        assert info.get("category") == "technical"

        # Get info for non-existent skill
        info = indexer.get_skill_info("NonExistentSkill")
        assert info == {}

    def test_skill_to_text(self, sample_skills, temp_dir):
        """Test skill to text conversion."""
        skills_file = os.path.join(temp_dir, "skills.json")
        with open(skills_file, 'w') as f:
            json.dump(sample_skills, f)

        indexer = VectorIndexer(use_openai=False, persist_dir=temp_dir)

        skill = sample_skills[0]
        text = indexer._skill_to_text(skill)

        assert skill["name"] in text
        assert skill["category"] in text
        if skill["aliases"]:
            for alias in skill["aliases"]:
                assert alias in text

    def test_index_update(self, sample_skills, temp_dir):
        """Test updating the index."""
        skills_file = os.path.join(temp_dir, "skills.json")
        with open(skills_file, 'w') as f:
            json.dump(sample_skills, f)

        indexer = VectorIndexer(
            use_openai=False,
            persist_dir=os.path.join(temp_dir, "chroma")
        )

        # Build initial index
        indexer.build_index(skills_file)
        stats1 = indexer.get_stats()

        # Update index
        indexer.update_index(skills_file, clear_existing=True)
        stats2 = indexer.get_stats()

        assert stats1['total_skills'] == stats2['total_skills']

    def test_empty_index(self, temp_dir):
        """Test behavior with empty skills list."""
        skills_file = os.path.join(temp_dir, "skills.json")
        with open(skills_file, 'w') as f:
            json.dump([], f)

        indexer = VectorIndexer(
            use_openai=False,
            persist_dir=os.path.join(temp_dir, "chroma")
        )

        indexer.build_index(skills_file)

        stats = indexer.get_stats()
        assert stats['total_skills'] == 0

    def test_nonexistent_skills_file(self, temp_dir):
        """Test error handling for non-existent skills file."""
        indexer = VectorIndexer(
            use_openai=False,
            persist_dir=os.path.join(temp_dir, "chroma")
        )

        with pytest.raises(FileNotFoundError):
            indexer.build_index("/nonexistent/skills.json")
