import requests

# Step 1 - Login to get token
login = requests.post("http://localhost:5000/api/auth/login", json={
    "email": "student@test.com",
    "password": "password123"
})

print("Login status:", login.status_code)
token = login.json()["access_token"]
print("Token received ✓")

# Step 2 - Upload CV
with open("test_cv.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:5000/api/students/upload-cv",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test_cv.pdf", f, "application/pdf")}
    )

print("Upload status:", response.status_code)
print("Response:", response.json())

# Step 3 - Register and login as employer
employer_register = requests.post("http://localhost:5000/api/auth/register", json={
    "email": "employer@test.com",
    "password": "password123",
    "role": "employer",
    "company_name": "Tech Ghana Ltd"
})
print("Employer register:", employer_register.json())

employer_login = requests.post("http://localhost:5000/api/auth/login", json={
    "email": "employer@test.com",
    "password": "password123"
})
employer_token = employer_login.json()["access_token"]

# Step 4 - Create internship
internship = requests.post(
    "http://localhost:5000/api/internships/",
    headers={"Authorization": f"Bearer {employer_token}"},
    json={
        "title": "Finance Intern",
        "description": "We need a finance intern with accounting and budgeting skills",
        "required_skills": ["accounting", "budgeting", "excel"],
        "location": "Accra",
        "duration": "3 months",
        "stipend": "GHS 500/month"
    }
)
print("Internship created:", internship.json())

# Step 5 - Get recommendations for student
recommendations = requests.get(
    "http://localhost:5000/api/matching/recommendations",
    headers={"Authorization": f"Bearer {token}"}
)
print("Recommendations:", recommendations.json())


chat = requests.post(
    "http://localhost:5000/api/chat/message",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "message": "What internships would suit someone with accounting skills?",
        "history": []
    }
)
print("Chatbot reply:", chat.json())