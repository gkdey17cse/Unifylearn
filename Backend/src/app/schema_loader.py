# def getSchemasAndSamples():
#     return {
#         "coursera": {
#             "fields": [
#                 "Course Title",
#                 "Course URL",
#                 "Brief Description",
#                 "Main Category",
#                 "Sub-Category",
#                 "Skills Covered",
#                 "Average Rating",
#                 "Estimated Duration",
#             ],
#             "sample": {
#                 "Course Title": "Machine Learning Specialization",
#                 "Course URL": "https://www.coursera.org/specializations/machine-learning",
#                 "Brief Description": "A beginner-friendly specialization covering supervised, unsupervised learning, and real-world ML projects.",
#                 "Main Category": "Data Science",
#                 "Sub-Category": "Machine Learning",
#                 "Skills Covered": "Python, TensorFlow, Supervised Learning, Unsupervised Learning",
#                 "Average Rating": "4.8/5",
#                 "Estimated Duration": "3 months (5 hours/week)",
#             },
#         },
#         "futurelearn": {
#             "fields": [
#                 "Course Title",
#                 "Course URL",
#                 "Brief Description",
#                 "Main Category",
#                 "Estimated Duration",
#             ],
#             "sample": {
#                 "Course Title": "Business Ethics: Exploring Big Data and Tax Avoidance",
#                 "Course URL": "https://www.futurelearn.com/courses/business-ethics",
#                 "Brief Description": "Learn how organizations use big data and handle ethical tax practices.",
#                 "Main Category": "Business & Management",
#                 "Estimated Duration": "2 weeks (3 hours/week)",
#             },
#         },
#         "simplilearn": {
#             "fields": [
#                 "Course Title",
#                 "Course URL",
#                 "Brief Description",
#                 "Main Category",
#                 "Skills Covered",
#             ],
#             "sample": {
#                 "Course Title": "Post Graduate Program in Cloud Computing",
#                 "Course URL": "https://www.simplilearn.com/cloud-computing-post-graduate-program",
#                 "Brief Description": "Master cloud computing with hands-on projects using AWS, Azure, and GCP.",
#                 "Main Category": "Cloud Computing",
#                 "Skills Covered": "AWS, Azure, Google Cloud, Cloud Architecture",
#             },
#         },
#         "udacity": {
#             "fields": [
#                 "Course Title",
#                 "Course URL",
#                 "Brief Description",
#                 "Estimated Duration",
#                 "Program Type",
#             ],
#             "sample": {
#                 "Course Title": "Getting Started with Google Workspace",
#                 "Course URL": "https://www.udacity.com/course/google-workspace-getting-started",
#                 "Brief Description": "Learn how to use Google Workspace tools for productivity and collaboration.",
#                 "Estimated Duration": "2 months (4 hours/week)",
#                 "Program Type": "Free Course",
#             },
#         },
#     }


# src/app/schema_loader.py
def getSchemasAndSamples():
    return {
        "coursera": {
            "fields": [
                "Title", "URL", "Short Intro", "Category", "Sub-Category", 
                "Skills", "Rating", "Duration", "Language", "Instructors",
                "Site", "Course Type", "Number of viewers", "Prequisites", "What you learn"
            ],
            "sample": {
                "Title": "Excel Skills for Business Specialization",
                "URL": "https://www.coursera.org/specializations/excel",
                "Short Intro": "Learn Excel Skills for Business. Master Excel to add a highly valuable asset to your employability portfolio.",
                "Category": "Business",
                "Sub-Category": "Business Essentials",
                "Skills": "Data Validation, Microsoft Excel, Microsoft Excel Macro, Pivot Table",
                "Rating": "4.9stars",
                "Duration": "Approximately 6 months to complete",
                "Language": "English",
                "Instructors": "Nicky Bull, Dr Prashan S. M. Karunaratne",
                "Site": "Coursera",
                "Course Type": "Specialization",
                "Number of viewers": "42,571"
            },
        },
        "udacity": {
            "fields": [
                "Title", "URL", "Short Intro", "Duration", "Program Type", 
                "Level", "Prequisites", "What you learn", "Site"
            ],
            "sample": {
                "Title": "Introduction to Computer Vision",
                "URL": "https://www.udacity.com/course/introduction-to-computer-vision--ud810",
                "Short Intro": "Offered at Georgia Tech as CS 6476",
                "Duration": "Estimated timeApprox. 4 Months",
                "Program Type": "Free Course",
                "Level": "Intermediate",
                "Prequisites": "Data structures, Python with NumPy, Linear algebra",
                "What you learn": "Image Processing, Camera Models, Feature Detection, Classification",
                "Site": "Udacity"
            },
        },
        "simplilearn": {
            "fields": [
                "Title", "URL", "Short Intro", "Category", "Course Type", 
                "Language", "Skills", "Instructors", "Site"
            ],
            "sample": {
                "Title": "CISSP Certification Training Course",
                "URL": "https://www.simplilearn.com/cyber-security/cissp-certification-training",
                "Short Intro": "Certified Information Systems Security Professional (CISSP) is a globally recognized certification for information technology security professionals.",
                "Category": "Simplilearn",
                "Course Type": "Ranked #1 Best Cybersecurity Bootcamp by Career Karma",
                "Language": "English",
                "Skills": "Information Security, Risk Management, Security Architecture",
                "Instructors": "Cyber Security Experts",
                "Site": "Simplilearn"
            },
        },
        "futurelearn": {
            "fields": [
                "Title", "URL", "Short Intro", "Duration", "Site", 
                "Weekly study", "Category", "Sub-Category"
            ],
            "sample": {
                "Title": "Emergency Planning and Preparedness: An Introduction",
                "URL": "https://www.futurelearn.com/courses/emergency-planning-preparedness",
                "Short Intro": "Explore the emergency planning process and learn how to develop emergency plans and preparedness frameworks.",
                "Duration": "2 weeks",
                "Site": "Future Learn",
                "Weekly study": "3 hours",
                "Category": "Business & Management",
                "Sub-Category": "Emergency Management"
            },
        },
    }