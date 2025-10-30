import requests

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJub25jZSI6Ikk5ZWpnT1QtaXQtVDJxMHB1eU5jZ0hJaFlVOGNNUlFlWnBsNlRRbXhHMjgiLCJhbGciOiJS"
FOLDER_PATH = "/Ticket-images"  # folder in OneDrive
IMAGE_FILE = "example.jpg"      # local image

with open(IMAGE_FILE, "rb") as f:
    image_data = f.read()

# OneDrive API upload URL
url = f"https://graph.microsoft.com/v1.0/me/drive/root:{FOLDER_PATH}/{IMAGE_FILE}:/content"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "image/jpeg"
}

res = requests.put(url, headers=headers, data=image_data)

if res.status_code in [200, 201]:
    print("Uploaded successfully")
else:
    print("Error:", res.text)
