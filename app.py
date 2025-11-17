from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import requests
from credentials import USERS
from onedrive_auth import get_token

app = Flask(__name__)
app.secret_key = "change_this_secret_key"

BASE_FOLDER = "/Ticket-images"
BACKUP_FOLDER = "/Ticket-backup"

# ======================================================
# LOGIN PAGE
# ======================================================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Validate credentials
        for user in USERS.values():
            if username == user["username"] and password == user["password"]:
                session["username"] = username
                session["role"] = user["role"]
                return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid username or password.")

    # If already logged in → go to dashboard
    if "role" in session:
        return redirect(url_for("dashboard"))

    return render_template("login.html")

# ======================================================
# LOGOUT
# ======================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ======================================================
# DASHBOARD
# ======================================================
@app.route("/dashboard")
def dashboard():
    if "role" not in session:
        return redirect(url_for("login"))

    return render_template("index.html",
                           role=session["role"],
                           username=session.get("username", "")
                           )

# ======================================================
# UPLOAD FILES WITHOUT DELETING OLD ONES
# ======================================================
@app.route("/upload", methods=["POST"])
def upload_files():
    if "role" not in session:
        return jsonify({"error": "Unauthorized"}), 403

    ticket = request.form.get("ticket_number", "").strip()
    files = request.files.getlist("images")

    if not ticket or not files:
        return jsonify({"error": "Ticket number and files are required"}), 400

    access_token = get_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    folder_path = f"{BASE_FOLDER}/{ticket}"

    # Create folder if missing
    create_folder = f"https://graph.microsoft.com/v1.0/me/drive/root:{BASE_FOLDER}:/children"
    requests.post(create_folder, headers={**headers, "Content-Type": "application/json"},
                  json={"name": ticket, "folder": {}, "@microsoft.graph.conflictBehavior": "replace"})

    uploaded = []
    for file in files:
        upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}/{file.filename}:/content"
        res = requests.put(upload_url, headers=headers, data=file.read())
        if res.status_code in [200, 201]:
            uploaded.append(file.filename)

    return jsonify({"uploaded": uploaded})

# ======================================================
# GET / VIEW MEDIA (checks both main + backup if office)
# ======================================================
@app.route("/get_media", methods=["POST"])
def get_media():
    if "role" not in session:
        return jsonify({"error": "Unauthorized"}), 403

    ticket = request.form.get("ticket_number", "").strip()
    if not ticket:
        return jsonify({"error": "No ticket specified"}), 400

    access_token = get_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    check_paths = [BASE_FOLDER]
    if session["role"] == "office":
        check_paths.append(BACKUP_FOLDER)

    images, videos = [], []

    for folder in check_paths:
        folder_path = f"{folder}/{ticket}"
        list_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}:/children"
        response = requests.get(list_url, headers=headers)

        if response.status_code == 200:
            for item in response.json().get("value", []):
                name = item["name"].lower()
                url = item["@microsoft.graph.downloadUrl"]
                if name.endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".heic")):
                    images.append(url)
                elif name.endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
                    videos.append(url)

    return jsonify({"images": images, "videos": videos})

# ======================================================
# BACKUP (OFFICE ONLY)
# ======================================================
@app.route("/backup", methods=["POST"])
def backup():
    if "role" not in session or session["role"] != "office":
        return jsonify({"error": "Unauthorized"}), 403

    ticket = request.form.get("ticket_number", "").strip()
    if not ticket:
        return jsonify({"error": "No ticket"}), 400

    access_token = get_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create backup folder
    requests.post(
        f"https://graph.microsoft.com/v1.0/me/drive/root:{BACKUP_FOLDER}:/children",
        headers={**headers, "Content-Type": "application/json"},
        json={"name": ticket, "folder": {}, "@microsoft.graph.conflictBehavior": "replace"}
    )

    # Copy files
    list_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{BASE_FOLDER}/{ticket}:/children"
    list_res = requests.get(list_url, headers=headers)

    if list_res.status_code == 200:
        for item in list_res.json().get("value", []):
            requests.post(
                f"https://graph.microsoft.com/v1.0/me/drive/items/{item['id']}/copy",
                headers=headers,
                json={"parentReference": {"path": f"/drive/root:{BACKUP_FOLDER}/{ticket}"}}
            )

    return jsonify({"success": True})

# ======================================================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)
