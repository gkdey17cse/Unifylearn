# src/app/schema_loader.py
def getSchemasAndSamples():
    return {
        "coursera": {
            "fields": [
                "Course Title",
                "Course URL",
                "Brief Description",
                "Main Category",
                "Sub-Category",
                "Skills Covered",
                "Average Rating",
                "Estimated Duration",
            ],
            "sample": {
                "Course Title": "Machine Learning Specialization",
                "Course URL": "https://www.coursera.org/specializations/machine-learning",
                "Brief Description": "A beginner-friendly specialization covering supervised, unsupervised learning, and real-world ML projects.",
                "Main Category": "Data Science",
                "Sub-Category": "Machine Learning",
                "Skills Covered": "Python, TensorFlow, Supervised Learning, Unsupervised Learning",
                "Average Rating": "4.8/5",
                "Estimated Duration": "3 months (5 hours/week)",
            },
        },
        "futurelearn": {
            "fields": [
                "Course Title",
                "Course URL",
                "Brief Description",
                "Main Category",
                "Estimated Duration",
            ],
            "sample": {
                "Course Title": "Business Ethics: Exploring Big Data and Tax Avoidance",
                "Course URL": "https://www.futurelearn.com/courses/business-ethics",
                "Brief Description": "Learn how organizations use big data and handle ethical tax practices.",
                "Main Category": "Business & Management",
                "Estimated Duration": "2 weeks (3 hours/week)",
            },
        },
        "simplilearn": {
            "fields": [
                "Course Title",
                "Course URL",
                "Brief Description",
                "Main Category",
                "Skills Covered",
            ],
            "sample": {
                "Course Title": "Post Graduate Program in Cloud Computing",
                "Course URL": "https://www.simplilearn.com/cloud-computing-post-graduate-program",
                "Brief Description": "Master cloud computing with hands-on projects using AWS, Azure, and GCP.",
                "Main Category": "Cloud Computing",
                "Skills Covered": "AWS, Azure, Google Cloud, Cloud Architecture",
            },
        },
        "udacity": {
            "fields": [
                "Course Title",
                "Course URL",
                "Brief Description",
                "Estimated Duration",
                "Program Type",
            ],
            "sample": {
                "Course Title": "Getting Started with Google Workspace",
                "Course URL": "https://www.udacity.com/course/google-workspace-getting-started",
                "Brief Description": "Learn how to use Google Workspace tools for productivity and collaboration.",
                "Estimated Duration": "2 months (4 hours/week)",
                "Program Type": "Free Course",
            },
        },
    }
