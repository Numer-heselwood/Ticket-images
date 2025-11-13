from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import requests
from io import BytesIO
from PIL import Image
from credentials import USERS  # <-- import usernames/passwords
from onedrive_auth import get_token

app = Flask(__name__)
app.secret_key = "super_secret_key_change_this"  # needed for sessions

BASE_FOLDER = "/Ticket-images"

# ==============================
# LOGIN SYSTEM
# ==============================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Check credentials
        for user_type, details in USERS.items():
            if username == details["username"] and password == details["password"]:
                session["role"] = details["role"]
                session["username"] = username
                return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid username or password.")

    if "role" in session:
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ==============================
# DASHBOARD
# ==============================
@app.route("/dashboard")
def dashboard():
    if "role" not in session:
        return redirect(url_for("login"))

    role = session["role"]
    return render_template("index.html", role=role, username=session["username"])


# ==============================
# UPLOAD IMAGES / VIDEOS
# ==============================
@app.route("/upload", methods=["POST"])
def upload_images():
    if "role" not in session:
        return jsonify({"error": "Unauthorized"}), 403

    ticket_number = request.form.get("ticket_number", "").strip()
    files = request.files.getlist("images")

    if not ticket_number or not files:
        return jsonify({"error": "Please provide ticket number and files"}), 400

    access_token = get_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    # Check or create folder
    folder_path = f"{BASE_FOLDER}/{ticket_number}"
    check_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}"
    check_res = requests.get(check_url, headers=headers)

    # If folder exists → delete old content
    if check_res.status_code == 200:
        list_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}:/children"
        list_res = requests.get(list_url, headers=headers)
        if list_res.status_code == 200:
            for item in list_res.json().get("value", []):
                del_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item['id']}"
                requests.delete(del_url, headers=headers)
    else:
        # Create folder if not exists
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


# ==============================
# FETCH IMAGES / VIDEOS
# ==============================
@app.route("/get_media", methods=["POST"])
def get_media():
    if "role" not in session:
        return jsonify({"error": "Unauthorized"}), 403

    ticket_number = request.form.get("ticket_number", "").strip()
    if not ticket_number:
        return jsonify({"error": "No ticket number provided"}), 400

    access_token = get_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    folder_path = f"{BASE_FOLDER}/{ticket_number}"
    list_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}:/children"

    response = requests.get(list_url, headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Unable to fetch media"}), response.status_code

    data = response.json()
    images = []
    videos = []

    for item in data.get("value", []):
        name = item["name"].lower()
        url = item["@microsoft.graph.downloadUrl"]
        if name.endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".heic")):
            images.append(url)
        elif name.endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
            videos.append(url)

    return jsonify({"images": images, "videos": videos})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)
