import requests

url = "http://107.191.45.46:3001/api/submissions/49"

headers = {
    "X-Auth-Token": "8EpLDbejCemFrqt6UWTiorLd7k1nG45tXoMeL4MFp4R",
    "Accept": "application/json"
}

response = requests.get(url, headers=headers)

#print("Status:", response.status_code)
#print("Text:", response.text)

submission = response.json()
print(submission)