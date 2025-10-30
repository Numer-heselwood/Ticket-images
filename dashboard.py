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
st.title("🎟️ Ticket Image System (Fast Mobile + Cache)")

# ==============================
# AUTO REFRESH
# ==============================
st_autorefresh(interval=REFRESH_INTERVAL_SEC * 1000, key="auto_refresh")

# ==============================
# SEARCH INTERFACE
# ==============================
search_query = st.text_input("🔍 Enter Ticket Number to View:", "")

@st.cache_data(show_spinner=False)
def download_and_prepare_image(url):
    """
    Download an image from OneDrive, convert HEIC to JPEG if needed,
    resize to thumbnail, and cache result.
    """
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content))

        # Convert HEIC or other unsupported formats to JPEG
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

        # Download images concurrently with caching
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
