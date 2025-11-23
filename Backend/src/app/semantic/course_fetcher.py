import os
from typing import List, Dict, Any
from src.app.db_connection import get_collection
from src.app.utils.logger import logger


class CourseFetcher:
    def __init__(self):
        self.providers = ["coursera", "udacity", "simplilearn", "futurelearn"]

    def fetch_all_courses(self, limit_per_provider: int = 1000) -> List[Dict]:
        """
        Fetch real courses from all 4 databases
        """
        all_courses = []
        total_count = 0

        for provider in self.providers:
            try:
                logger.semantic(f"📂 Fetching courses from {provider}...")
                collection = get_collection(provider)

                # Fetch courses from this provider
                provider_courses = list(collection.find().limit(limit_per_provider))

                # Convert to standardized format
                standardized_courses = self._standardize_courses(
                    provider_courses, provider
                )
                all_courses.extend(standardized_courses)

                logger.semantic(
                    f"✅ Fetched {len(standardized_courses)} courses from {provider}"
                )
                total_count += len(standardized_courses)

            except Exception as e:
                logger.error(f"❌ Failed to fetch from {provider}: {e}")
                continue

        logger.semantic(f"🎯 Total courses fetched: {total_count}")
        return all_courses

    def _standardize_courses(
        self, raw_courses: List[Dict], provider: str
    ) -> List[Dict]:
        """
        Convert provider-specific course format to standardized format
        """
        standardized = []

        for course in raw_courses:
            try:
                # Generate unique ID
                course_id = f"{provider}_{str(course.get('_id', ''))}"

                # Standardize fields based on provider schema
                standardized_course = {
                    "id": course_id,
                    "provider": provider,
                    "title": self._get_field(course, provider, "title"),
                    "description": self._get_field(course, provider, "description"),
                    "skills": self._get_skills(course, provider),
                    "category": self._get_field(course, provider, "category"),
                    "what_you_learn": self._get_field(
                        course, provider, "what_you_learn"
                    ),
                    "raw_data": course,  # Keep original for reference
                }

                standardized.append(standardized_course)

            except Exception as e:
                logger.warning(f"Failed to standardize course from {provider}: {e}")
                continue

        return standardized

    def _get_field(self, course: Dict, provider: str, field_type: str) -> str:
        """
        Get field value based on provider-specific field names
        """
        field_mapping = {
            "coursera": {
                "title": ["Title", "Course Title"],
                "description": ["Short Intro", "Brief Description", "Description"],
                "category": ["Category", "Main Category"],
                "what_you_learn": ["What you learn", "Skills"],
            },
            "udacity": {
                "title": ["Title", "Course Title"],
                "description": ["Short Intro", "Brief Description"],
                "category": ["Category"],
                "what_you_learn": ["What you learn", "Skills Covered"],
            },
            "simplilearn": {
                "title": ["Title", "Course Title"],
                "description": ["Short Intro", "Brief Description"],
                "category": ["Category"],
                "what_you_learn": ["Skills", "What you learn"],
            },
            "futurelearn": {
                "title": ["Title", "Course Title"],
                "description": ["Short Intro", "Brief Description"],
                "category": ["Category", "Main Category"],
                "what_you_learn": ["What you learn"],
            },
        }

        # Try all possible field names for this provider and field type
        possible_fields = field_mapping.get(provider, {}).get(field_type, [field_type])

        for field in possible_fields:
            if field in course and course[field]:
                value = course[field]
                if isinstance(value, str) and value.strip():
                    return value.strip()
                elif isinstance(value, list):
                    return " ".join([str(item) for item in value if item])

        return ""  # Return empty if not found

    def _get_skills(self, course: Dict, provider: str) -> List[str]:
        """
        Extract skills list from course data
        """
        skills = []

        # Try different field names for skills
        skill_fields = {
            "coursera": ["Skills", "What you learn"],
            "udacity": ["What you learn", "Skills"],
            "simplilearn": ["Skills"],
            "futurelearn": ["What you learn"],
        }

        possible_fields = skill_fields.get(provider, ["Skills"])

        for field in possible_fields:
            if field in course and course[field]:
                skills_data = course[field]
                if isinstance(skills_data, str):
                    # Split comma-separated skills
                    skills.extend(
                        [
                            skill.strip()
                            for skill in skills_data.split(",")
                            if skill.strip()
                        ]
                    )
                elif isinstance(skills_data, list):
                    skills.extend(
                        [str(skill).strip() for skill in skills_data if skill]
                    )
                break

        return skills


# Global instance
course_fetcher = CourseFetcher()
