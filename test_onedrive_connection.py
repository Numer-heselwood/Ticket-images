import requests
import json

# =====================================================
# Your OneDrive API Access Token
# =====================================================
ACCESS_TOKEN = """eyJ0eXAiOiJKV1QiLCJub25jZSI6ImJBRTFBWjJBTnV4Z1RWc0tJdDRtVnVTOXY2Z0hvZDlxOFJ5UWd1YzlOWTgiLCJhbGciOiJSUzI1NiIsIng1dCI6InlFVXdtWFdMMTA3Q2MtN1FaMldTYmVPYjNzUSIsImtpZCI6InlFVXdtWFdMMTA3Q2MtN1FaMldTYmVPYjNzUSJ9.eyJhdWQiOiIwMDAwMDAwMy0wMDAwLTAwMDAtYzAwMC0wMDAwMDAwMDAwMDAiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9iNTI3MGU1OS0wNjExLTQ3ZGMtYjhkOS04MjkzOTViZjgxMTkvIiwiaWF0IjoxNzYxNzMzNjY2LCJuYmYiOjE3NjE3MzM2NjYsImV4cCI6MTc2MTczODQ1NiwiYWNjdCI6MCwiYWNyIjoiMSIsImFjcnMiOlsicDEiXSwiYWlvIjoiQVdRQW0vOGFBQUFBaDBiai81Qmtta1NXSW1PMy9Db3J1RkpBYVlzWTFMbU1FT0didGQyN295YmhhMVI2djNTMU9qemZ5Yml0OU9RNkJyNWxuR0pmamo0VnlMcjA4dkROZWRzSEJvaThlRzl0SUxnSGFubytBcHJIaXN5SlBoM3BmcTd0YVI5WHo2M2wiLCJhbXIiOlsicHdkIiwibWZhIl0sImFwcF9kaXNwbGF5bmFtZSI6IlRpY2tldERhc2hib2FyZCIsImFwcGlkIjoiZTcxZTg1NzUtYzE1Ni00MTk5LWJiNTYtZDc0ZTZiMDJmM2JjIiwiYXBwaWRhY3IiOiIwIiwiZmFtaWx5X25hbWUiOiJLaGFuIiwiZ2l2ZW5fbmFtZSI6Ik51bWVyIiwiaWR0eXAiOiJ1c2VyIiwiaXBhZGRyIjoiMmEwMDoyM2VlOjE4Yjg6ODBkZTpiZGFmOjZiNzY6MzMyOjNmMTAiLCJuYW1lIjoiTnVtZXIgS2hhbiIsIm9pZCI6IjVjNTc4NDk5LTk1NWUtNDBjZi1iY2I4LTgyNTgzYjNhOGYzOSIsInBsYXRmIjoiMTQiLCJwdWlkIjoiMTAwMzIwMDUyN0FCRkI3MiIsInJoIjoiMS5BUk1CV1E0bnRSRUczRWU0MllLVGxiLUJHUU1BQUFBQUFBQUF3QUFBQUFBQUFBQTZBYmdUQVEuIiwic2NwIjoiRmlsZXMuUmVhZFdyaXRlLkFsbCBVc2VyLlJlYWQgcHJvZmlsZSBvcGVuaWQgZW1haWwiLCJzaWQiOiIwMDlhYzE0OS05NjU1LWZmZTMtZmUxMC1hMDk4MmNhZDY0OGMiLCJzaWduaW5fc3RhdGUiOlsia21zaSJdLCJzdWIiOiJsdlZJVno4WmZpMmdrZGRETS1DX0VEZmNMRWZ1bzFTcDh0TDh2Nlo1dzhnIiwidGVuYW50X3JlZ2lvbl9zY29wZSI6IkVVIiwidGlkIjoiYjUyNzBlNTktMDYxMS00N2RjLWI4ZDktODI5Mzk1YmY4MTE5IiwidW5pcXVlX25hbWUiOiJudW1lci5raGFuQGhlc2Vsd29vZC5jb20iLCJ1cG4iOiJudW1lci5raGFuQGhlc2Vsd29vZC5jb20iLCJ1dGkiOiJNV0otNTMxVkprNjVwdmxOVkhSbEFBIiwidmVyIjoiMS4wIiwid2lkcyI6WyIxNThjMDQ3YS1jOTA3LTQ1NTYtYjdlZi00NDY1NTFhNmI1ZjciLCI5Yjg5NWQ5Mi0yY2QzLTQ0YzctOWQwMi1hNmFjMmQ1ZWE1YzMiLCJjZjFjMzhlNS0zNjIxLTQwMDQtYTdjYi04Nzk2MjRkY2VkN2MiLCJiNzlmYmY0ZC0zZWY5LTQ2ODktODE0My03NmIxOTRlODU1MDkiXSwieG1zX2FjZCI6MTc2MTczMzI3OSwieG1zX2FjdF9mY3QiOiI5IDMiLCJ4bXNfZnRkIjoiV1MzYTJCMFY1VE9QRnZMZFRNWWVKOWNhc1NycnNrcjh3WVNSTE83bTFCUUJaWFZ5YjNCbGJtOXlkR2d0WkhOdGN3IiwieG1zX2lkcmVsIjoiMSAxOCIsInhtc19zdCI6eyJzdWIiOiIxbVZiV0xxR3pfYXNpbEhYYXZ2cURpS193LVJnMXdwUVBmUGEtcl8xVHU4In0sInhtc19zdWJfZmN0IjoiMyAyIiwieG1zX3RjZHQiOjE3NTMxMDk1NzEsInhtc190bnRfZmN0IjoiMyAxMCJ9.HQIdVdE54v46Ql4B-eIKZyiBLEtH3gzFeioMeDkxgBT81a_S5gDeArtvLBMxMKAkYPBhlKGzkBO_Fu9WnEQX4-mZ6auxnOoNHay5ihfVIszTmqHEG8Ug3fd_UMt6ymSpDsX2-FFrdWXOS8lE_xdoWp-PfU7KYJIcn-iVj6ICcLK7MC05lJmE70FhuolpQ61xs5ZeXvQghSFhFNzmSMbH1qIuOPQrdVIdbj27VL1aePY2xVllzcRNvsk83s_ww79shRfTN4Y1bfI9jxOY5URXHlMNfvw072mm72TZtuCmFF3jRwWdGjYQQ3piLKeTeeXnRgZgWAXLrxfbm4RpEGhXzg"""

# =====================================================
# OneDrive folder to test
# =====================================================
FOLDER_PATH = "/Ticket-images"

url = f"https://graph.microsoft.com/v1.0/me/drive/root:{FOLDER_PATH}:/children"
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

print("🔍 Checking OneDrive connection...\n")

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    print("✅ Connected successfully! Found items:\n")
    for item in data.get("value", []):
        print("-", item["name"])
elif response.status_code == 401:
    print("❌ Unauthorized (401) — Your token may have expired or is invalid.")
    print(json.dumps(response.json(), indent=2))
else:
    print(f"❌ Error {response.status_code}")
    print(json.dumps(response.json(), indent=2))
