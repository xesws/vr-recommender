"""
Data models for Stage 1 - Data Collection Module
"""

from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class Course:
    """CMU Course data model"""
    course_id: str           # "95-865"
    title: str               # "Unstructured Data Analytics"
    department: str          # "Heinz College"
    description: str
    units: int
    prerequisites: List[str]
    learning_outcomes: List[str]

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class VRApp:
    """VR App data model"""
    app_id: str              # 唯一标识
    name: str                # "Spatial"
    category: str            # "Productivity"
    description: str
    features: List[str]
    skills_developed: List[str]
    rating: float
    price: str

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
