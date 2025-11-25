
import json
import os

def fix_courses():
    path = "data_collection/data/courses.json"
    
    with open(path, 'r') as f:
        courses = json.load(f)
    
    # Check if 15-112 exists
    for c in courses:
        if c['course_id'] == '15-112':
            print("15-112 already exists.")
            return

    print("Adding 15-112...")
    new_course = {
        "course_id": "15-112",
        "title": "Fundamentals of Programming and Computer Science",
        "department": "School of Computer Science",
        "description": "A technical introduction to the fundamentals of programming with an emphasis on producing clear, robust, and reasonably efficient code using top-down design, informal analysis, and effective testing and debugging. Starting from first principles, we will cover a large subset of the Python programming language, including its standard libraries and programming paradigms.",
        "units": 12,
        "prerequisites": [],
        "learning_outcomes": []
    }
    courses.append(new_course)
    
    with open(path, 'w') as f:
        json.dump(courses, f, indent=2)
    print("Done.")

if __name__ == "__main__":
    fix_courses()
