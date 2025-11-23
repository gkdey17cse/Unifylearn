# src/app/query_generator/semantic_enhancer.py
from typing import Dict, Any, List
from src.app.semantic.semantic_expander import semantic_expander
from src.app.utils.logger import logger


class SemanticQueryEnhancer:
    def __init__(self):
        self.expander = semantic_expander

    def enhance_user_query(self, user_query: str) -> Dict[str, Any]:
        """
        Enhanced semantic expansion with AI domain understanding and priority ordering
        """
        try:
            # Get semantic expansion
            expansion_result = self.expander.expand_query(user_query)

            # Extract main concepts with domain awareness
            main_concepts = self._extract_main_concepts(user_query, expansion_result)

            # Extract level and provider info
            level_info = self._extract_level_info(user_query, expansion_result)

            enhanced_data = {
                "original_query": user_query,
                "expanded_terms": expansion_result["expanded_terms"],
                "main_concepts": main_concepts,
                "level": level_info,
                "providers": self._detect_providers(user_query),
            }

            logger.semantic(f"Enhanced query: {enhanced_data}")

            return enhanced_data

        except Exception as e:
            logger.error(f"Semantic enhancement failed: {e}")
            # Fallback with basic structure
            return {
                "original_query": user_query,
                "expanded_terms": [],
                "main_concepts": [user_query],
                "level": "any",
                "providers": ["coursera", "udacity", "simplilearn", "futurelearn"],
            }

    def _extract_main_concepts(
        self, user_query: str, expansion_result: Dict
    ) -> List[str]:
        """Extract main technical concepts from the query"""
        concepts = []

        # Look for technical terms in expanded terms
        technical_terms = [
            "ai",
            "machine learning",
            "deep learning",
            "artificial intelligence",
            "data science",
            "python",
            "web development",
            "cloud",
            "cybersecurity",
            "nlp",
            "natural language processing",
            "computer vision",
            "neural networks",
            "reinforcement learning",
            "llm",
            "large language models",
            "transformers",
            "computer vision",
            "generative ai",
        ]

        for term in expansion_result["expanded_terms"]:
            term_lower = term.lower()
            if any(tech_term in term_lower for tech_term in technical_terms):
                if term_lower not in [c.lower() for c in concepts]:
                    concepts.append(term)

        # If no technical concepts found, use the original query words
        if not concepts:
            words = user_query.lower().split()
            concepts = [
                word
                for word in words
                if len(word) > 3 and word not in ["show", "me", "for", "courses"]
            ]

        return concepts if concepts else [user_query]

    def _extract_level_info(self, user_query: str, expansion_result: Dict) -> str:
        """Extract course level information"""
        query_lower = user_query.lower()
        expansion_lower = [term.lower() for term in expansion_result["expanded_terms"]]

        beginner_terms = [
            "beginner",
            "beginners",
            "introductory",
            "introduction",
            "basic",
            "foundation",
            "getting started",
            "fundamentals",
        ]
        advanced_terms = [
            "advanced",
            "expert",
            "professional",
            "master",
            "deep",
            "specialized",
            "comprehensive",
        ]

        if any(
            term in query_lower or any(term in exp for exp in expansion_lower)
            for term in beginner_terms
        ):
            return "beginner"
        elif any(
            term in query_lower or any(term in exp for exp in expansion_lower)
            for term in advanced_terms
        ):
            return "advanced"
        else:
            return "any"

    def _detect_providers(self, user_query: str) -> List[str]:
        """Detect if specific providers are mentioned"""
        query_lower = user_query.lower()
        providers = ["coursera", "udacity", "simplilearn", "futurelearn"]

        mentioned_providers = []
        for provider in providers:
            if provider in query_lower:
                mentioned_providers.append(provider)

        return mentioned_providers if mentioned_providers else providers


# Global instance
semantic_enhancer = SemanticQueryEnhancer()
