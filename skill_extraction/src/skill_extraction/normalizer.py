"""Skill name normalization and standardization"""

import re
from typing import Optional


class SkillNormalizer:
    """Normalizes and standardizes skill names"""

    def __init__(self):
        """Initialize with comprehensive alias mappings"""
        # Comprehensive alias map for skill name normalization
        self.alias_map = {
            # Machine Learning & AI
            "ml": "Machine Learning",
            "ai": "Artificial Intelligence",
            "artificial intelligence": "Artificial Intelligence",
            "dl": "Deep Learning",
            "deep learning": "Deep Learning",
            "nlp": "Natural Language Processing",
            "natural language processing": "Natural Language Processing",
            "computer vision": "Computer Vision",
            "cv": "Computer Vision",

            # Programming & Development
            "programming": "Programming",
            "coding": "Programming",
            "python": "Python",
            "py": "Python",
            "sql": "SQL",
            "r": "R Programming",
            "r programming": "R Programming",
            "javascript": "JavaScript",
            "js": "JavaScript",
            "java": "Java",
            "c++": "C++",
            "cpp": "C++",
            "c#": "C#",
            "csharp": "C#",
            "go": "Go",
            "golang": "Go",
            "rust": "Rust",
            "scala": "Scala",

            # Data & Analytics
            "data analysis": "Data Analysis",
            "data analytics": "Data Analytics",
            "analytics": "Analytics",
            "data science": "Data Science",
            "statistics": "Statistics",
            "statistical analysis": "Statistical Analysis",
            "pandas": "Pandas",
            "numpy": "NumPy",
            "tableau": "Tableau",
            "power bi": "Power BI",
            "excel": "Excel",
            "spreadsheets": "Spreadsheets",

            # Software Engineering
            "swe": "Software Engineering",
            "software engineering": "Software Engineering",
            "se": "Software Engineering",
            "software development": "Software Development",
            "web development": "Web Development",
            "frontend": "Frontend Development",
            "backend": "Backend Development",
            "fullstack": "Full Stack Development",
            "full-stack": "Full Stack Development",
            "api": "API Development",
            "rest api": "REST API",
            "graphql": "GraphQL",
            "microservices": "Microservices",
            "devops": "DevOps",
            "ci/cd": "CI/CD",

            # Database
            "database": "Database Management",
            "db": "Database Management",
            "dbms": "Database Management",
            "mongodb": "MongoDB",
            "postgres": "PostgreSQL",
            "postgresql": "PostgreSQL",
            "mysql": "MySQL",
            "redis": "Redis",
            "sqlite": "SQLite",

            # Cloud & Infrastructure
            "cloud computing": "Cloud Computing",
            "aws": "AWS",
            "azure": "Azure",
            "gcp": "Google Cloud Platform",
            "google cloud": "Google Cloud Platform",
            "docker": "Docker",
            "kubernetes": "Kubernetes",
            "k8s": "Kubernetes",

            # Business & Management
            "pm": "Project Management",
            "project management": "Project Management",
            "product management": "Product Management",
            "agile": "Agile",
            "scrum": "Scrum",
            "kanban": "Kanban",
            "waterfall": "Waterfall",

            # UX/UI & Design
            "ux": "User Experience",
            "ui": "User Interface",
            "user experience": "User Experience",
            "user interface": "User Interface",
            "ux/ui": "UX/UI Design",
            "design thinking": "Design Thinking",
            "figma": "Figma",
            "photoshop": "Adobe Photoshop",
            "adobe": "Adobe Creative Suite",

            # Finance & Economics
            "finance": "Finance",
            "financial analysis": "Financial Analysis",
            "financial modeling": "Financial Modeling",
            "accounting": "Accounting",
            "economics": "Economics",
            "econometrics": "Econometrics",
            "blockchain": "Blockchain",
            "cryptocurrency": "Cryptocurrency",
            "fintech": "FinTech",
            "risk management": "Risk Management",

            # Public Policy & Social Sciences
            "public policy": "Public Policy",
            "policy analysis": "Policy Analysis",
            "policy": "Public Policy",
            "government": "Government",
            "public administration": "Public Administration",
            "nonprofit": "Nonprofit Management",
            "ngo": "Nonprofit Management",

            # Security
            "cybersecurity": "Cybersecurity",
            "infosec": "Information Security",
            "information security": "Information Security",
            "security": "Cybersecurity",
            "ethical hacking": "Ethical Hacking",
            "penetration testing": "Penetration Testing",
            "security analysis": "Security Analysis",

            # Communication & Leadership
            "communication": "Communication",
            "public speaking": "Public Speaking",
            "presentation": "Presentation",
            "leadership": "Leadership",
            "team management": "Team Management",
            "management": "Management",
            "negotiation": "Negotiation",
            "conflict resolution": "Conflict Resolution",

            # Research & Analysis
            "research": "Research",
            "research methods": "Research Methods",
            "survey design": "Survey Design",
            "qualitative research": "Qualitative Research",
            "quantitative research": "Quantitative Research",
            "data collection": "Data Collection",

            # Business Intelligence
            "bi": "Business Intelligence",
            "business intelligence": "Business Intelligence",
            "kpi": "KPI Development",
            "dashboard": "Dashboard Development",
            "reporting": "Reporting",

            # Marketing
            "marketing": "Marketing",
            "digital marketing": "Digital Marketing",
            "seo": "Search Engine Optimization",
            "sem": "Search Engine Marketing",
            "social media": "Social Media Marketing",
            "content marketing": "Content Marketing",

            # Healthcare
            "healthcare": "Healthcare",
            "public health": "Public Health",
            "epidemiology": "Epidemiology",

            # Education
            "education": "Education",
            "curriculum": "Curriculum Development",
            "instructional design": "Instructional Design",

            # Mathematics
            "math": "Mathematics",
            "calculus": "Calculus",
            "linear algebra": "Linear Algebra",
            "algebra": "Algebra",
            "geometry": "Geometry",
            "discrete math": "Discrete Mathematics",

            # Other
            "machine learning": "Machine Learning",
            "data mining": "Data Mining",
            "big data": "Big Data",
            "etl": "ETL",
            "data warehouse": "Data Warehousing",
            "data visualization": "Data Visualization",
            "storytelling": "Data Storytelling",
        }

        # Category keywords for auto-classification
        self.category_keywords = {
            "technical": [
                "programming", "coding", "python", "sql", "javascript", "java", "c++",
                "machine learning", "ai", "deep learning", "data science", "analytics",
                "statistics", "database", "sql", "aws", "cloud", "docker", "kubernetes",
                "api", "web development", "software", "devops", "ci/cd", "git", "github",
                "algorithms", "data structure", "testing", "debugging", "agile", "scrum"
            ],
            "soft": [
                "communication", "leadership", "teamwork", "collaboration", "management",
                "presentation", "public speaking", "writing", "critical thinking",
                "problem solving", "decision making", "negotiation", "conflict resolution",
                "time management", "project management", "organization", "creativity",
                "adaptability", "mentoring", "coaching"
            ],
            "domain": [
                "finance", "economics", "accounting", "marketing", "sales", "healthcare",
                "education", "public policy", "government", "nonprofit", "retail",
                "manufacturing", "logistics", "supply chain", "human resources",
                "operations", "strategy", "entrepreneurship", "consulting"
            ]
        }

    def normalize(self, skill_name: str) -> str:
        """
        Normalize a skill name to standard form

        Args:
            skill_name: Raw skill name

        Returns:
            Standardized skill name
        """
        # Clean and lowercase for comparison
        cleaned = skill_name.lower().strip()

        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Check alias map (exact match)
        if cleaned in self.alias_map:
            return self.alias_map[cleaned]

        # Check for whole word matches in alias map (more precise)
        words = re.findall(r'\b\w+\b', cleaned)

        for alias, standard in self.alias_map.items():
            # Skip very short aliases (like "r") to avoid false matches
            if len(alias) < 2:
                continue

            # Check if alias appears as a whole word
            if re.search(r'\b' + re.escape(alias) + r'\b', cleaned):
                return standard

        # Title case for consistency
        return skill_name.strip().title()

    def are_similar(self, skill1: str, skill2: str) -> bool:
        """
        Check if two skills are similar enough to be merged

        Args:
            skill1: First skill name
            skill2: Second skill name

        Returns:
            True if skills are similar
        """
        s1 = self.normalize(skill1).lower()
        s2 = self.normalize(skill2).lower()

        # Exact match
        if s1 == s2:
            return True

        # One is subset of the other
        if s1 in s2 or s2 in s1:
            return True

        # Check alias mappings
        if s1 in self.alias_map and self.alias_map[s1].lower() == s2:
            return True
        if s2 in self.alias_map and self.alias_map[s2].lower() == s1:
            return True

        return False

    def get_category(self, skill_name: str) -> str:
        """
        Auto-classify skill into category based on keywords

        Args:
            skill_name: Skill name

        Returns:
            Category: "technical", "soft", or "domain"
        """
        normalized = self.normalize(skill_name).lower()

        # Check explicit categories first
        for cat, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in normalized or normalized in keyword:
                    return cat

        # Default to technical
        return "technical"
