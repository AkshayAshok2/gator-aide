import requests
import json
#THIS FILE IS A SHELL OR TUTORIAL FOR HOW IT LOOKS LIKE ACCESSING THE CANVAS API
#CANVAS API DOCUMENTATION LINK 1: https://auckland.test.instructure.com/doc/api/api-docs.json
#CANVAS API DOCUMENTATION LINK 2: https://ufldev.test.instructure.com/doc/api/users.json
CANVAS_API_DEV_TOKEN = '18024~GB2WcCRLAVe36FLhK4F3CQyvXPQCEym7PrFaDV7k6crfJv6L29HaxE6XrvTWEKBZ'
CANVAS_API_TEST_TOKEN = '18024~kLm7ETCVZ9Zv7EvHBwt4BQexwRc2mrwaYDycxJMFRZUK4YrnDxfcAatmYQYHt38H'

headers = {'Authorization': f'Bearer {CANVAS_API_DEV_TOKEN}'}
url = 'https://ufldev.instructure.com/api/v1/courses/'
course_id = '180/'

r = requests.get(url, headers = headers)
print("=== First API Call ===")
print('status code: ')
print(r.status_code)
#print(r.text)
print(r.json())
print()
print()
# 1) Get course details (like you already did)
course_details_url = f"{url}/{course_id}"
resp_course = requests.get(course_details_url, headers=headers)
print("=== Course Details ===")
print("Status Code:", resp_course.status_code)
print(resp_course.json())
print()

# 2) Get assignments
assignments_url = f"{url}/{course_id}/assignments"
resp_assignments = requests.get(assignments_url, headers=headers)
print("=== Assignments ===")
print("Status Code:", resp_assignments.status_code)
print(resp_assignments.json())
print()

# 3) Get modules
modules_url = f"{url}/{course_id}/modules"
resp_modules = requests.get(modules_url, headers=headers)
print("=== Modules ===")
print("Status Code:", resp_modules.status_code)
print(resp_modules.json())
print()

# 4) Get module items (requires a specific module_id)
# e.g., if you know a module ID (like 123), you can do:
# module_items_url = f"{url}/{course_id}/modules/123/items"
# resp_module_items = requests.get(module_items_url, headers=headers)

# 5) Get discussions (topics)
discussions_url = f"{url}/{course_id}/discussion_topics"
resp_discussions = requests.get(discussions_url, headers=headers)
print("=== Discussion Topics ===")
print("Status Code:", resp_discussions.status_code)
print(resp_discussions.json())
print()

# 6) (Optional) Filter for announcements only
# Canvas announcements are discussion topics with the "is_announcement" flag or by query param
announcements_url = f"{url}/{course_id}/discussion_topics?only_announcements=true"
resp_announcements = requests.get(announcements_url, headers=headers)
print("=== Announcements ===")
print("Status Code:", resp_announcements.status_code)
print(resp_announcements.json())
print()

# 7) Get course users (people in the course)
users_url = f"{url}/{course_id}/users"
resp_users = requests.get(users_url, headers=headers)
print("=== Course Users ===")
print("Status Code:", resp_users.status_code)
resp_users_json = resp_users.json()
print(resp_users_json)
print()
for user in resp_users_json:
    print('Name: ')
    print(user['name'])
print()

# 8) Get quizzes
quizzes_url = f"{url}/{course_id}/quizzes"
resp_quizzes = requests.get(quizzes_url, headers=headers)
print("=== Quizzes ===")
print("Status Code:", resp_quizzes.status_code)
print(resp_quizzes.json())
print()

#9) Get smartsearch api calls
smartsearch_url = f"{url}/{course_id}/smartsearch"
params = {
    "q": "What are key details in the syllabus", 
  
}
resp_smartsearch = requests.get(smartsearch_url, headers=headers, params=params)
print("=== Smartsearch ===")
print("Status Code:", resp_smartsearch.status_code)
print(resp_smartsearch.json())
resp_smartsearch_json = resp_smartsearch.json()
print()
print()
print("=== Filtered Smartsearch ===")
filtered_results = [
    item for item in resp_smartsearch_json["results"] if item["distance"] <= 0.55
]
resp_smartsearch_json["results"] = filtered_results
print(resp_smartsearch_json)


# 9) Get enrollment details for the course
'''enrollments_url = f"{url}/{course_id}/enrollments"
resp_enrollments = requests.get(enrollments_url, headers=headers)
print("=== Enrollments ===")
print("Status Code:", resp_enrollments.status_code)
print(resp_enrollments.json())
print()'''