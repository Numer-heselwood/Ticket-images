import os
import requests
from io import BytesIO
from PIL import Image
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from onedrive_auth import get_token
import concurrent.futures

# ==============================
# CONFIGURATION
# ==============================
BASE_FOLDER = "/Ticket-images"
REFRESH_INTERVAL_SEC = 30  # auto-refresh interval in seconds
MAX_WORKERS = 5  # concurrent downloads
THUMBNAIL_SIZE = (400, 400)  # display size

st.set_page_config(page_title="Ticket Dashboard", layout="wide")
st.title("🎟️ Ticket Image System (Upload + Fast Mobile Viewer)")

# Tabs: Upload + Dashboard
tab1, tab2 = st.tabs(["📤 Upload Images", "🖼️ Dashboard Viewer"])

# ==============================
# 📤 TAB 1 — UPLOAD IMAGES
# ==============================
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

        # Ensure folder exists
        folder_path = f"{BASE_FOLDER}/{ticket_number}"
        check_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}"
        check_res = requests.get(check_url, headers=headers)

        if check_res.status_code == 404:
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

        # Upload files
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

# ==============================
# 🖼️ TAB 2 — DASHBOARD VIEWER
# ==============================
with tab2:
    st.header("Ticket Image Dashboard")
    st_autorefresh(interval=REFRESH_INTERVAL_SEC * 1000, key="auto_refresh")

    search_query = st.text_input("🔍 Enter Ticket Number to View:", "")

    @st.cache_data(show_spinner=False)
    def download_and_prepare_image(url):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content))
            if img.format == "HEIC":
                img = img.convert("RGB")
            img.thumbnail(THUMBNAIL_SIZE)
            return img
        except Exception:
            return None

    if search_query.strip():
        access_token = get_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        folder_path = f"{BASE_FOLDER}/{search_query.strip()}"
        list_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}:/children"

        try:
            response = requests.get(list_url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            st.error(f"⚠️ Error retrieving images: {e}")
            st.stop()

        data = response.json()
        items = [item for item in data.get("value", []) if item["name"].lower().endswith(
            (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".heic"))]

        if items:
            st.success(f"📸 Found {len(items)} image(s) for ticket {search_query.strip()}")

            # Download images concurrently
            image_objs = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [executor.submit(download_and_prepare_image, item["@microsoft.graph.downloadUrl"])
                           for item in items]
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    img = future.result()
                    if img:
                        image_objs.append((i, img, items[i]["name"]))

            # Display in 3-column layout
            cols = st.columns(3)
            for idx, img, name in image_objs:
                cols[idx % 3].image(img, caption=name, use_container_width=True)
        else:
            st.warning("No images found in this folder.")
    else:
        st.info("Enter a ticket number to view images.")

    st.markdown(
        f"""
        <hr>
        <div style='text-align:center; color:gray;'>
        ⏱️ Auto-refreshes every {REFRESH_INTERVAL_SEC}s • Images stored in OneDrive • Ticket folders are separate • Cached for faster mobile loading
        </div>
        """,
        unsafe_allow_html=True,
    )
