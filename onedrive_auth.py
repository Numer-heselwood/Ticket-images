# onedrive_auth.py
import os
import json
from msal import PublicClientApplication, SerializableTokenCache

# === CONFIGURATION ===
CLIENT_ID = "e71e8575-c156-4199-bb56-d74e6b02f3bc"
TENANT_ID = "b5270e59-0611-47dc-b8d9-829395bf8119"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["Files.ReadWrite.All", "User.Read"]  # scopes for OneDrive
CACHE_PATH = "token_cache.bin"

# === HELPER FUNCTIONS ===
def load_cache():
    """Load token cache from file."""
    cache = SerializableTokenCache()
    if os.path.exists(CACHE_PATH):
        try:
            cache.deserialize(open(CACHE_PATH, "r").read())
        except Exception as e:
            print(f"⚠️ Could not deserialize cache: {e}")
    return cache

def save_cache(cache):
    """Save token cache to file."""
    if cache and getattr(cache, "has_state_changed", False):
        try:
            with open(CACHE_PATH, "w") as f:
                f.write(cache.serialize())
        except Exception as e:
            print(f"⚠️ Could not save cache: {e}")

def get_token():
    """Get a valid access token for OneDrive. Uses device flow if needed."""
    cache = load_cache()
    app = PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)

    # Try to get token silently first
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            save_cache(cache)
            return result["access_token"]

    # If silent acquisition fails, use device flow
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise Exception("❌ Device flow failed. Check client_id/tenant_id and permissions.")

    print("\nGo to:", flow["verification_uri"])
    print("Enter code:", flow["user_code"])

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        save_cache(cache)
        return result["access_token"]
    else:
        print("❌ Authentication failed.")
        print(json.dumps(result, indent=2))
        return None
