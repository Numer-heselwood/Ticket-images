import os
import time
import requests
from datetime import datetime
from io import BytesIO
from PIL import Image
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from onedrive_auth import get_token

# ==============================
# CONFIGURATION
# ==============================
BASE_FOLDER = "/Ticket-images"
DAYS_TO_KEEP = 14
REFRESH_INTERVAL_SEC = 30  # auto-refresh every 30 sec

st.set_page_config(page_title="Ticket Dashboard", layout="wide")
st.title("🎟️ Ticket Image System")

# Tabs: Upload + Dashboard
tab1, tab2 = st.tabs(["📤 Upload Images", "🖼️ Dashboard Viewer"])

# ============================================================
# 📤 TAB 1 — UPLOAD IMAGES TO ONEDRIVE
# ============================================================
with tab1:
    st.header("Upload New Ticket Images")

    ticket_number = st.text_input("🎫 Enter Ticket Number:")
    uploaded_files = st.file_uploader(
        "📸 Upload one or more images",
        type=["jpg", "jpeg", "png", "bmp", "tiff", "heic"],
        accept_multiple_files=True,
    )

    def upload_to_onedrive(ticket_number, files):
        access_token = get_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        # Step 1️⃣ Ensure folder exists
        folder_path = f"{BASE_FOLDER}/{ticket_number}"
        check_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}"
        check_res = requests.get(check_url, headers=headers)

        if check_res.status_code == 404:
            # Folder not found — create it
            create_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{BASE_FOLDER}:/children"
            folder_data = {
                "name": ticket_number,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename"
            }
            create_res = requests.post(
                create_url,
                headers={**headers, "Content-Type": "application/json"},
                json=folder_data
            )
            if create_res.status_code not in [200, 201]:
                st.error(f"❌ Could not create folder for {ticket_number}. Error: {create_res.text}")
                return
            else:
                st.success(f"📁 Created folder for ticket {ticket_number}")
        elif check_res.status_code != 200:
            st.error(f"❌ Error checking folder: {check_res.text}")
            return

        # Step 2️⃣ Upload files
        for file in files:
            file_name = file.name
            upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}/{file_name}:/content"
            upload_res = requests.put(upload_url, headers=headers, data=file.read())

            if upload_res.status_code in [200, 201]:
                st.success(f"✅ Uploaded {file_name}")
            else:
                st.error(f"❌ Failed to upload {file_name}: {upload_res.text}")

    if st.button("⬆️ Upload Images"):
        if not ticket_number.strip():
            st.warning("Please enter a ticket number first.")
        elif not uploaded_files:
            st.warning("Please upload at least one image.")
        else:
            with st.spinner("Uploading to OneDrive..."):
                upload_to_onedrive(ticket_number.strip(), uploaded_files)
            st.success("🎉 All images uploaded successfully!")

# ============================================================
# 🖼️ TAB 2 — DASHBOARD VIEWER
# ============================================================
with tab2:
    st.header("Ticket Image Dashboard")

    st_autorefresh(interval=REFRESH_INTERVAL_SEC * 1000, key="auto_refresh")

    search_query = st.text_input("🔍 Enter Ticket Number to View:", "")

    if search_query.strip():
        access_token = get_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        folder_path = f"{BASE_FOLDER}/{search_query.strip()}"
        list_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}:/children"
        response = requests.get(list_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            images = [item for item in data.get("value", []) if item["name"].lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".heic"))]

            if images:
                st.success(f"📸 Found {len(images)} image(s) for ticket {search_query.strip()}")
                cols = st.columns(3)
                for i, item in enumerate(images):
                    image_url = item["@microsoft.graph.downloadUrl"]
                    img_data = requests.get(image_url).content
                    img = Image.open(BytesIO(img_data))
                    cols[i % 3].image(img, caption=item["name"], use_container_width=True)
            else:
                st.warning("No images found in this folder.")
        elif response.status_code == 404:
            st.warning("❌ No folder found for that ticket number.")
        else:
            st.error(f"⚠️ Error retrieving images: {response.text}")
    else:
        st.info("Enter a ticket number to view images.")

    st.markdown(
        f"""
        <hr>
        <div style='text-align:center; color:gray;'>
        ⏱️ Auto-refreshes every {REFRESH_INTERVAL_SEC}s • Images stored in OneDrive • Keeps each ticket in its own folder
        </div>
        """,
        unsafe_allow_html=True,
    )
