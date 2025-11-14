ESSENTIAL_FIELDS = [
    "title",
    "url", 
    "description",
    "category",
    "language",
    "skills",
    "instructors",
    "duration",
    "site",
    "level",
    "viewers",
    "prerequisites",
    "learning_outcomes",
    "price",
]

# Field mapping from original to universal schema - focused on essentials
FIELD_MAPPING = {
    "title": ["Title", "Course Title", "Name"],
    "url": ["URL", "Course URL", "Link"],
    "description": ["Short Intro", "Brief Description", "Course Short Intro", "Description"],
    "category": ["Category", "Main Category"],
    "language": ["Language"],
    "skills": ["Skills", "Skills Covered", "What you learn"],
    "instructors": ["Instructors"],
    "duration": ["Duration", "Estimated Duration", "Weekly study"],
    "site": ["Site", "Platform"],
    "level": ["Level", "Course Type", "Difficulty", "Program Type"],
    "viewers": ["Number of viewers", "Enrollments", "Students"],
    "prerequisites": ["Prequisites", "Requirements"],
    "learning_outcomes": ["What you learn", "Learning Outcomes", "You will learn"],
    "price": ["Price", "Premium course", "Cost"],
}

__all__ = ["ESSENTIAL_FIELDS", "FIELD_MAPPING"]