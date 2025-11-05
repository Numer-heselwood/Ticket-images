from flask import Flask, render_template, request, jsonify
import requests
from onedrive_auth import get_token

app = Flask(__name__)

BASE_FOLDER = "/Ticket-images"


@app.route("/")
def index():
    """Main page with both tabs: Upload and View."""
    return render_template("index.html")


# ✅ Route used to check if a ticket folder already exists
@app.route("/check_ticket", methods=["POST"])
def check_ticket():
    ticket_number = request.form.get("ticket_number", "").strip()
    if not ticket_number:
        return jsonify({"error": "No ticket number provided"}), 400

    access_token = get_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    folder_path = f"{BASE_FOLDER}/{ticket_number}"
    check_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}"

    response = requests.get(check_url, headers=headers)
    if response.status_code == 200:
        return jsonify({"exists": True})
    elif response.status_code == 404:
        return jsonify({"exists": False})
    else:
        return jsonify({"error": "Unable to check folder status"}), response.status_code


# ✅ Upload new images (and optionally replace old ones)
@app.route("/upload", methods=["POST"])
def upload_images():
    ticket_number = request.form.get("ticket_number", "").strip()
    files = request.files.getlist("images")

    if not ticket_number or not files:
        return jsonify({"error": "Please provide ticket number and images"}), 400

    access_token = get_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    folder_path = f"{BASE_FOLDER}/{ticket_number}"

    # Check if folder exists
    check_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}"
    check_res = requests.get(check_url, headers=headers)

    # If exists, delete all existing files before uploading new ones
    if check_res.status_code == 200:
        list_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}:/children"
        list_res = requests.get(list_url, headers=headers)
        if list_res.status_code == 200:
            items = list_res.json().get("value", [])
            for item in items:
                del_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item['id']}"
                requests.delete(del_url, headers=headers)
    else:
        # Create folder if it doesn't exist
        create_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{BASE_FOLDER}:/children"
        folder_data = {
            "name": ticket_number,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }
        requests.post(create_url, headers={**headers, "Content-Type": "application/json"}, json=folder_data)

    # Upload new files
    uploaded = []
    for file in files:
        file_name = file.filename
        upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}/{file_name}:/content"
        upload_res = requests.put(upload_url, headers=headers, data=file.read())
        if upload_res.status_code in [200, 201]:
            uploaded.append(file_name)

    return jsonify({"uploaded": uploaded})


# ✅ Fetch images for the view tab
@app.route("/get_images", methods=["POST"])
def get_images():
    ticket_number = request.form.get("ticket_number", "").strip()
    if not ticket_number:
        return jsonify({"error": "No ticket number provided"}), 400

    access_token = get_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    folder_path = f"{BASE_FOLDER}/{ticket_number}"
    list_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}:/children"

    response = requests.get(list_url, headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Unable to fetch images"}), response.status_code

    data = response.json()
    images = [
        item["@microsoft.graph.downloadUrl"]
        for item in data.get("value", [])
        if item["name"].lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".heic"))
    ]

    return jsonify({"images": images})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
