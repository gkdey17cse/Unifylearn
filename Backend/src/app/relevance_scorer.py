# src/app/relevance_scorer.py - COMPLETE VERSION
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
        """Extract key terms from user query"""
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
        }

        # Clean and tokenize
        words = re.findall(r"\b[a-zA-Z]{3,}\b", query.lower())
        key_terms = [word for word in words if word not in stopwords]

        return list(set(key_terms))  # Remove duplicates

    def calculate_field_relevance(
        self, field_value: str, key_terms: List[str], field_weight: float = 1.0
    ) -> float:
        """Calculate relevance score for a specific field"""
        if not field_value or not key_terms:
            return 0.0

        field_text = str(field_value).lower()
        total_score = 0.0

        for term in key_terms:
            # Exact match bonus
            if f" {term} " in f" {field_text} ":
                total_score += 2.0
            # Partial match
            elif term in field_text:
                total_score += 1.0
            # Similarity-based matching
            else:
                # Check for similar terms using Jaro-Winkler
                for word in field_text.split():
                    similarity = self.jaro_winkler_similarity(term, word)
                    if similarity > 0.8:  # High similarity threshold
                        total_score += similarity

        return (total_score / len(key_terms)) * field_weight

    def calculate_course_relevance(
        self, course_data: Dict[str, Any], user_query: str, key_terms: List[str]
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate overall relevance score for a course with detailed breakdown"""

        # Define field weights based on importance for relevance
        field_weights = {
            "Title": 3.0,  # Highest weight - most important
            "What you learn": 2.5,  # High weight - describes content
            "Skills": 2.0,  # High weight - key skills
            "Short Intro": 1.5,  # Medium weight - description
            "Category": 1.5,  # Medium weight - category
            "Sub-Category": 1.0,  # Lower weight - subcategory
        }

        total_score = 0.0
        field_scores = {}
        max_possible_score = sum(field_weights.values())

        # Calculate score for each field
        for field, weight in field_weights.items():
            field_value = course_data.get(field, "")
            if field_value:
                field_score = self.calculate_field_relevance(
                    field_value, key_terms, weight
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

        # Normalize score to 0-1 range
        normalized_score = total_score / (
            max_possible_score + 2.0
        )  # +2 for cosine score weight

        return min(normalized_score, 1.0), field_scores  # Cap at 1.0

    def softmax(self, scores: List[float]) -> List[float]:
        """Apply softmax function to convert scores to probabilities"""
        if not scores:
            return []

        # Subtract max for numerical stability
        max_score = max(scores)
        exp_scores = [math.exp(score - max_score) for score in scores]
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
            top_courses = ranked_courses[:5]
            logger.info("🏆 TOP 5 COURSES BY RELEVANCE:")
            for i, (course, prob, score, _) in enumerate(top_courses):
                title = course.get("Title", "Unknown")[:50]
                logger.info(
                    f"   {i+1}. Prob: {prob:.4f} | Score: {score:.4f} | {title}"
                )

        return ranked_courses


# Global instance
relevance_scorer = RelevanceScorer()
