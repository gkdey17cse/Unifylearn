import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
import pickle
from typing import List, Dict, Any, Tuple
from src.app.utils.logger import logger
from src.app.semantic.course_fetcher import course_fetcher


class SemanticQueryExpander:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize semantic expander with pre-trained model
        No training required - uses zero-shot understanding
        """
        logger.semantic(f"Loading pre-trained model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embeddings_cache = {}
        self.course_metadata = {}
        self.embeddings_loaded = False

        # Enhanced skill synonyms with comprehensive AI/ML terms
        self.skill_synonyms = {
            "ai": [
                "artificial intelligence",
                "machine learning",
                "deep learning",
                "neural networks",
                "natural language processing",
                "nlp",
                "computer vision",
                "reinforcement learning",
                "large language models",
                "llm",
                "generative ai",
                "transformers",
                "cognitive computing",
            ],
            "machine learning": [
                "ai",
                "ml",
                "deep learning",
                "neural networks",
                "supervised learning",
                "unsupervised learning",
                "reinforcement learning",
                "predictive modeling",
                "statistical learning",
            ],
            "ml": ["machine learning", "ai", "deep learning"],
            "deep learning": [
                "neural networks",
                "cnn",
                "rnn",
                "lstm",
                "transformer",
                "computer vision",
                "convolutional neural networks",
                "recurrent neural networks",
            ],
            "data science": [
                "data analysis",
                "analytics",
                "big data",
                "data mining",
                "statistics",
                "python",
                "r",
                "sql",
                "pandas",
                "numpy",
                "data visualization",
            ],
            "beginner": [
                "beginners",
                "introductory",
                "foundation",
                "basic",
                "getting started",
                "first steps",
            ],
            "beginers": ["beginners", "beginner", "introductory"],
            "coruses": ["courses", "programs", "classes", "training"],
            "python": [
                "python programming",
                "django",
                "flask",
                "data science",
                "machine learning",
            ],
            "javascript": [
                "js",
                "node.js",
                "react",
                "web development",
                "frontend",
                "backend",
            ],
            "cloud": [
                "aws",
                "azure",
                "google cloud",
                "cloud computing",
                "cloud services",
                "infrastructure",
            ],
            "programming": ["coding", "software development", "computer science"],
            "database": ["sql", "nosql", "mongodb", "database management"],
            "cybersecurity": ["security", "information security", "network security"],
            "web development": [
                "frontend",
                "backend",
                "full stack",
                "web design",
                "html css",
                "javascript",
            ],
            "nlp": [
                "natural language processing",
                "text mining",
                "sentiment analysis",
                "language models",
            ],
            "computer vision": [
                "image processing",
                "object detection",
                "image recognition",
            ],
        }

        # Embeddings storage path
        self.embeddings_dir = "./data/embeddings"
        os.makedirs(self.embeddings_dir, exist_ok=True)

    def initialize_with_real_data(self, force_refresh: bool = False):
        """
        Initialize with REAL courses from all databases
        """
        if self.embeddings_loaded and not force_refresh:
            return

        # Try to load existing embeddings first
        if not force_refresh:
            self._load_embeddings()
            if self.embeddings_loaded:
                logger.semantic("✅ Loaded existing embeddings from disk")
                return

        # Fetch real courses from all databases
        logger.semantic("🔄 Fetching real courses from all databases...")
        all_courses = course_fetcher.fetch_all_courses()

        if not all_courses:
            logger.error("❌ No courses fetched from databases!")
            return

        # Precompute embeddings
        self.precompute_course_embeddings(all_courses)
        logger.semantic("✅ Initialized with REAL course data")

    def precompute_course_embeddings(self, courses: List[Dict]):
        """
        Precompute embeddings for REAL courses
        """
        logger.semantic(
            f"🔄 Precomputing embeddings for {len(courses)} REAL courses..."
        )

        successful = 0
        failed = 0

        for course in courses:
            try:
                course_id = course["id"]
                text_to_embed = self._prepare_course_text(course)

                if not text_to_embed or len(text_to_embed.strip()) < 10:
                    failed += 1
                    continue

                # Generate embedding
                embedding = self.model.encode([text_to_embed])[0]
                self.embeddings_cache[course_id] = embedding
                self.course_metadata[course_id] = course
                successful += 1

            except Exception as e:
                failed += 1
                continue

        self.embeddings_loaded = True
        logger.semantic(
            f"✅ Precomputed embeddings for {successful} courses, {failed} failed"
        )

        # Save embeddings for future use
        self._save_embeddings()

    def _prepare_course_text(self, course: Dict) -> str:
        """
        Combine relevant course fields for semantic understanding
        Uses REAL course data from databases
        """
        text_parts = []

        # Add title (most important)
        if course.get("title"):
            text_parts.append(course["title"])

        # Add description
        if course.get("description"):
            text_parts.append(course["description"])

        # Add skills
        if course.get("skills"):
            if isinstance(course["skills"], list):
                text_parts.extend(course["skills"])
            else:
                text_parts.append(str(course["skills"]))

        # Add category
        if course.get("category"):
            text_parts.append(course["category"])

        # Add "what you learn" content
        if course.get("what_you_learn"):
            text_parts.append(str(course["what_you_learn"]))

        # Filter out empty parts and join
        clean_parts = [
            str(part).strip() for part in text_parts if part and str(part).strip()
        ]

        if not clean_parts:
            return ""

        final_text = " ".join(clean_parts)
        return final_text

    def expand_query(
        self, user_query: str, similarity_threshold: float = 0.3
    ) -> Dict[str, Any]:
        """
        Main method: Expand user query with semantic alternatives
        """
        logger.semantic(f"Expanding query: '{user_query}'")

        # Step 1: Basic keyword expansion with spelling correction
        expanded_terms = self._expand_with_synonyms(user_query)

        # Step 2: Semantic expansion using embeddings
        semantic_terms = self._expand_with_semantics(user_query, similarity_threshold)

        # Combine all terms
        all_terms = list(set(expanded_terms + semantic_terms))

        # Remove the original query terms to avoid duplication
        original_terms = user_query.lower().split()
        final_terms = [term for term in all_terms if term not in original_terms]

        # Filter out very long terms and irrelevant ones
        filtered_terms = [
            term for term in final_terms if len(term) < 50 and len(term) > 2
        ]

        # Sort by relevance
        filtered_terms.sort(key=lambda x: (len(x), x))

        logger.semantic(f"Original: '{user_query}' → Expanded: {filtered_terms}")

        return {
            "original_query": user_query,
            "expanded_terms": filtered_terms,
            "expansion_count": len(filtered_terms),
        }

    def _expand_with_synonyms(self, query: str) -> List[str]:
        """Expand query using predefined synonyms with spelling correction"""
        query_lower = query.lower()
        expanded = []

        # First, handle common spelling mistakes
        spelling_corrections = {
            "coruses": "courses",
            "beginers": "beginners",
            "programing": "programming",
            "devlopment": "development",
            "lernin": "learning",
            "lerning": "learning",
            "maching": "machine",
        }

        corrected_query = query_lower
        for wrong, correct in spelling_corrections.items():
            if wrong in corrected_query:
                corrected_query = corrected_query.replace(wrong, correct)
                expanded.append(correct)  # Add the corrected term

        # Check each word in the query against our synonym dictionary
        for word in corrected_query.split():
            if word in self.skill_synonyms:
                expanded.extend(self.skill_synonyms[word])

        # Also check multi-word phrases
        for phrase, synonyms in self.skill_synonyms.items():
            if phrase in corrected_query and len(phrase) > 2:
                expanded.extend(synonyms)

        return list(set(expanded))

    def _expand_with_semantics(self, query: str, threshold: float) -> List[str]:
        """Find semantically related terms using course embeddings"""
        if not self.embeddings_loaded:
            logger.semantic("No embeddings loaded, using synonym expansion only")
            return []

        query_embedding = self.model.encode([query])[0]
        similar_terms = set()

        for course_id, course_embedding in self.embeddings_cache.items():
            similarity = cosine_similarity([query_embedding], [course_embedding])[0][0]

            if similarity > threshold:
                course = self.course_metadata[course_id]
                # Extract relevant terms from similar course
                terms = self._extract_terms_from_course(course)
                similar_terms.update(terms)

        return list(similar_terms)

    def _extract_terms_from_course(self, course: Dict) -> List[str]:
        """Extract meaningful terms from a course"""
        terms = set()

        # Extract from title (individual words, 3-20 chars)
        title_terms = course.get("title", "").lower().split()
        terms.update([term for term in title_terms if 3 <= len(term) <= 20])

        # Extract skills (most valuable)
        skills = course.get("skills", [])
        if isinstance(skills, list):
            # Filter skills to reasonable length
            terms.update([skill.lower() for skill in skills if 2 <= len(skill) <= 30])
        elif isinstance(skills, str):
            skill_list = [skill.strip().lower() for skill in skills.split(",")]
            terms.update([skill for skill in skill_list if 2 <= len(skill) <= 30])

        # Extract category (single words usually)
        category = course.get("category", "").lower()
        if category and 3 <= len(category) <= 25:
            # Split category into individual words if it's a phrase
            if " " in category:
                terms.update(
                    [word for word in category.split() if 3 <= len(word) <= 20]
                )
            else:
                terms.add(category)

        return list(terms)

    def _save_embeddings(self):
        """Save embeddings to disk for persistence"""
        try:
            embeddings_path = os.path.join(self.embeddings_dir, "course_embeddings.pkl")
            with open(embeddings_path, "wb") as f:
                pickle.dump(
                    {
                        "embeddings_cache": self.embeddings_cache,
                        "course_metadata": self.course_metadata,
                    },
                    f,
                )
        except Exception as e:
            logger.error(f"Failed to save embeddings: {e}")

    def _load_embeddings(self):
        """Load embeddings from disk"""
        try:
            embeddings_path = os.path.join(self.embeddings_dir, "course_embeddings.pkl")
            if os.path.exists(embeddings_path):
                with open(embeddings_path, "rb") as f:
                    data = pickle.load(f)
                    self.embeddings_cache = data["embeddings_cache"]
                    self.course_metadata = data["course_metadata"]
                    self.embeddings_loaded = True
        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")


# Global instance
semantic_expander = SemanticQueryExpander()
