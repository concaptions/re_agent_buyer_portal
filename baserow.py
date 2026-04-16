import requests

url = "https://baserow.intevoai.com/api/database/rows/table/684/"

params = {
    "user_field_names": "true",
    "filter__Buyer Phone__equal": "1234567890"
}

headers = {
    "Authorization": "Token 86aZji1ZIvGQ0hcgoi4I1qDWGiRWv7Bn"
}

response = requests.get(url, headers=headers, params=params)

print(response.json())