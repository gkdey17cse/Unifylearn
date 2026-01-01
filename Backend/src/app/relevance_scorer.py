# src/app/relevance_scorer.py - COMPLETELY FIXED VERSION
import re
import math
from typing import Dict, List, Any, Tuple
from difflib import SequenceMatcher
import jellyfish
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from src.app.utils.logger import logger


class RelevanceScorer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)

    def jaro_winkler_similarity(self, s1: str, s2: str) -> float:
        """Calculate Jaro-Winkler similarity between two strings"""
        try:
            return jellyfish.jaro_winkler_similarity(s1.lower(), s2.lower())
        except:
            return 0.0

    def levenshtein_similarity(self, s1: str, s2: str) -> float:
        """Calculate normalized Levenshtein similarity"""
        try:
            distance = jellyfish.levenshtein_distance(s1.lower(), s2.lower())
            max_len = max(len(s1), len(s2))
            if max_len == 0:
                return 1.0
            return 1 - (distance / max_len)
        except:
            return 0.0

    def cosine_similarity_score(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts"""
        try:
            if not text1.strip() or not text2.strip():
                return 0.0

            tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
            return similarity[0][0]
        except Exception as e:
            logger.debug(f"Cosine similarity failed: {e}")
            return 0.0

    def extract_key_terms(self, query: str) -> List[str]:
        """Extract key terms from user query with technology prioritization"""
        # Remove common stopwords and extract meaningful terms
        stopwords = {
            "course",
            "courses",
            "find",
            "show",
            "me",
            "get",
            "want",
            "need",
            "learn",
            "learning",
            "any",
            "with",
            "only",
            "from",
            "platform",
            "platforms",
            "some",
            "that",
            "teach",
            "also",
            "classes",
        }

        # Clean and tokenize
        words = re.findall(r"\b[a-zA-Z]{3,}\b", query.lower())
        key_terms = [word for word in words if word not in stopwords]

        return list(set(key_terms))

    def calculate_technology_match_score(
        self, field_value: str, technology_terms: List[str]
    ) -> float:
        """Calculate score for specific technology matches with higher weights"""
        if not field_value or not technology_terms:
            return 0.0

        field_text = str(field_value).lower()
        total_score = 0.0

        # Technology-specific scoring - prioritize exact matches
        for tech in technology_terms:
            tech_lower = tech.lower()

            # Exact phrase match (highest weight)
            if f" {tech_lower} " in f" {field_text} ":
                total_score += 5.0  # Increased weight for exact matches

            # Word boundary match (high weight)
            elif re.search(rf"\b{re.escape(tech_lower)}\b", field_text):
                total_score += 3.0

            # Partial match (medium weight)
            elif tech_lower in field_text:
                total_score += 1.5

            # Similarity-based matching (lower weight)
            else:
                max_similarity = 0.0
                for word in field_text.split():
                    similarity = self.jaro_winkler_similarity(tech_lower, word)
                    if similarity > 0.85:  # Higher threshold for technology terms
                        max_similarity = max(max_similarity, similarity)

                total_score += max_similarity * 0.5

        return total_score

    def calculate_field_relevance(
        self,
        field_value: str,
        key_terms: List[str],
        technology_terms: List[str],
        field_weight: float = 1.0,
    ) -> float:
        """Calculate relevance score for a specific field"""
        if not field_value or (not key_terms and not technology_terms):
            return 0.0

        field_text = str(field_value).lower()
        total_score = 0.0

        # Calculate technology-specific score (higher priority)
        tech_score = self.calculate_technology_match_score(field_text, technology_terms)
        total_score += tech_score

        # Calculate general term score (lower priority)
        if key_terms:
            general_score = 0.0
            for term in key_terms:
                term_lower = term.lower()

                # Exact match bonus
                if f" {term_lower} " in f" {field_text} ":
                    general_score += 2.0
                # Partial match
                elif term_lower in field_text:
                    general_score += 1.0
                # Similarity-based matching
                else:
                    max_similarity = 0.0
                    for word in field_text.split():
                        similarity = self.jaro_winkler_similarity(term_lower, word)
                        if similarity > 0.8:
                            max_similarity = max(max_similarity, similarity)

                    general_score += max_similarity

            total_score += (
                general_score / len(key_terms)
            ) * 0.5  # Reduce general term weight

        return total_score * field_weight

    def identify_technology_terms(self, key_terms: List[str]) -> List[str]:
        """Identify technology-specific terms that should be prioritized"""
        technology_keywords = {
            # Web Development
            "javascript",
            "react",
            "angular",
            "vue",
            "node",
            "html",
            "css",
            "typescript",
            "frontend",
            "backend",
            "fullstack",
            "web",
            # Programming Languages
            "python",
            "java",
            "c++",
            "c#",
            "ruby",
            "php",
            "swift",
            "kotlin",
            "go",
            "rust",
            # Data Science
            "sql",
            "nosql",
            "mongodb",
            "postgresql",
            "mysql",
            "redis",
            # Mobile
            "android",
            "ios",
            "flutter",
            "reactnative",
            # Cloud & DevOps
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "jenkins",
            # AI/ML
            "tensorflow",
            "pytorch",
            "keras",
            "scikit",
            "pandas",
            "numpy",
        }

        return [term for term in key_terms if term.lower() in technology_keywords]

    def identify_level_terms(self, key_terms: List[str]) -> List[str]:
        """Identify course level terms"""
        level_keywords = {
            "beginner",
            "intermediate",
            "advanced",
            "basic",
            "fundamental",
            "intro",
        }
        return [term for term in key_terms if term.lower() in level_keywords]

    def calculate_course_relevance(
        self, course_data: Dict[str, Any], user_query: str, key_terms: List[str]
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate overall relevance score for a course with detailed breakdown"""

        # Identify technology and level terms for special handling
        technology_terms = self.identify_technology_terms(key_terms)
        level_terms = self.identify_level_terms(key_terms)

        logger.info(f"🎯 Technology terms: {technology_terms}")
        logger.info(f"🎯 Level terms: {level_terms}")

        # Enhanced field weights - technology-focused fields get higher weights
        field_weights = {
            "Title": 4.0,  # Highest weight - most important for tech matching
            "What you learn": 3.0,  # High weight - describes technical content
            "Skills": 3.0,  # High weight - key technical skills
            "Short Intro": 2.0,  # Medium weight - description
            "Category": 1.5,  # Medium weight - category
            "Sub-Category": 1.0,  # Lower weight - subcategory
            "Level": 2.0,  # Special weight for level matching
        }

        total_score = 0.0
        field_scores = {}

        # Calculate score for each field with technology prioritization
        for field, weight in field_weights.items():
            field_value = course_data.get(field, "")
            if field_value:
                # Special handling for Level field
                if field == "Level" and level_terms:
                    level_score = (
                        self.calculate_technology_match_score(field_value, level_terms)
                        * weight
                    )
                    field_scores[field] = level_score
                    total_score += level_score
                else:
                    field_score = self.calculate_field_relevance(
                        field_value, key_terms, technology_terms, weight
                    )
                    field_scores[field] = field_score
                    total_score += field_score

        # Calculate overall text similarity using cosine similarity
        combined_text = " ".join(
            [
                str(course_data.get("Title", "")),
                str(course_data.get("Short Intro", "")),
                str(course_data.get("What you learn", "")),
                str(course_data.get("Skills", "")),
            ]
        )

        cosine_score = self.cosine_similarity_score(user_query, combined_text)
        total_score += cosine_score * 2.0  # Add cosine score with weight
        field_scores["cosine_similarity"] = cosine_score * 2.0

        # Bonus for courses that match ALL technology terms
        if technology_terms:
            all_tech_matched = True
            combined_tech_text = combined_text.lower()
            for tech in technology_terms:
                if tech.lower() not in combined_tech_text:
                    all_tech_matched = False
                    break

            if all_tech_matched:
                total_score += 3.0  # Significant bonus for matching all technologies
                field_scores["all_tech_bonus"] = 3.0

        # Normalize score to prevent extreme values
        max_possible_score = (
            sum(field_weights.values()) + 2.0 + 3.0
        )  # fields + cosine + bonus
        normalized_score = total_score / max_possible_score

        return min(normalized_score, 1.0), field_scores

    def softmax(self, scores: List[float]) -> List[float]:
        """Apply softmax function to convert scores to probabilities with temperature"""
        if not scores:
            return []

        # Use temperature to make probabilities more spread out
        temperature = 0.05  # Lower temperature = more spread out probabilities

        # Subtract max for numerical stability and apply temperature
        max_score = max(scores)
        exp_scores = [math.exp((score - max_score) / temperature) for score in scores]
        sum_exp_scores = sum(exp_scores)

        return [exp_score / sum_exp_scores for exp_score in exp_scores]

    def rank_courses_by_relevance(
        self, courses: List[Dict[str, Any]], user_query: str
    ) -> List[Tuple[Dict[str, Any], float, float, Dict[str, float]]]:
        """Rank courses by relevance to user query and return with softmax probabilities and detailed scores"""
        if not courses:
            return []

        logger.info(f"🔍 Calculating relevance scores for {len(courses)} courses")

        # Extract key terms from user query
        key_terms = self.extract_key_terms(user_query)
        logger.info(f"🧠 Extracted key terms: {key_terms}")

        # Calculate raw relevance scores with detailed breakdown
        scored_courses = []
        for course in courses:
            relevance_score, field_scores = self.calculate_course_relevance(
                course, user_query, key_terms
            )
            scored_courses.append((course, relevance_score, field_scores))

        # Sort by relevance score (descending)
        scored_courses.sort(key=lambda x: x[1], reverse=True)

        # Extract scores for softmax
        raw_scores = [score for _, score, _ in scored_courses]

        # Apply softmax to get probabilities
        probabilities = self.softmax(raw_scores)

        # Combine courses with their probabilities and detailed scores
        ranked_courses = []
        for (course, relevance_score, field_scores), probability in zip(
            scored_courses, probabilities
        ):
            ranked_courses.append((course, probability, relevance_score, field_scores))

        # Log top results for debugging
        if ranked_courses:
            top_courses = ranked_courses[:10]
            logger.info("🏆 TOP 10 COURSES BY RELEVANCE:")
            for i, (course, prob, score, field_scores) in enumerate(top_courses):
                title = course.get("Title", "Unknown")[:60]
                provider = course.get("_provider", "unknown")
                tech_score = (
                    field_scores.get("Title", 0)
                    + field_scores.get("Skills", 0)
                    + field_scores.get("What you learn", 0)
                )
                logger.info(
                    f"   {i+1}. [{provider.upper():<12}] Prob: {prob:.4f} | Tech Score: {tech_score:.2f} | {title}"
                )

        return ranked_courses


# Global instance
relevance_scorer = RelevanceScorer()
