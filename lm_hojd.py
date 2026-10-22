import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# ASSET_TYPE = "thumbnail"
ASSET_TYPE = "data"
COLLECTION_ID = "dtm-cog"
OUTPUT_DIR = os.getenv("LM_OUTPUT_DIR") or "assets"

# Get credentials from environment variables
username = os.getenv("LM_USERNAME")
password = os.getenv("LM_PASSWORD")
if not username or not password:
    raise ValueError("LM_USERNAME and LM_PASSWORD environment variables must be set")

# Create auth tuple for requests
auth = (username, password)


### Swagger setup
def load_swagger_spec(path):
    with open(path, "r") as f:
        return json.load(f)


def create_endpoint_url(base_url, path):
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


swagger_spec = load_swagger_spec("swagger.json")
base_url = swagger_spec["servers"][0]["url"]

collection_items_endpoint = create_endpoint_url(
    base_url, "/collections/{collection_id}/items?limit={limit}"
)
### End swagger setup

# Get items in the collection
collection_items_response = requests.get(
    collection_items_endpoint.format(collection_id=COLLECTION_ID, limit=10000)
)
collection_items_as_json = collection_items_response.json()

# Download assets for each item in the collection
for feature in collection_items_as_json["features"]:
    asset = feature["assets"][ASSET_TYPE]
    asset_url = asset["href"]
    expected_size = asset.get("file:size")
    filename = asset_url.split("/")[-1]
    filepath = os.path.join(OUTPUT_DIR, filename)
    partpath = filepath + ".part"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Skip if file already exists and is complete
    if os.path.exists(filepath):
        if expected_size is None or os.path.getsize(filepath) == expected_size:
            print("Skipping", filename, "- already exists")
            continue
        print("Redownloading", filename, "- incomplete file")

    # Download asset to a .part file and rename it when complete, so an
    # interrupted download never leaves a file that looks finished
    print("Downloading", filename)
    try:
        with requests.get(asset_url, auth=auth, stream=True) as response:
            if response.status_code != 200:
                print(f"Error downloading {filename} - HTTP {response.status_code}")
                continue
            with open(partpath, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)

        if expected_size is not None and os.path.getsize(partpath) != expected_size:
            print(f"Error downloading {filename} - size mismatch")
            os.remove(partpath)
            continue

        os.replace(partpath, filepath)
        print("Done downloading", filename)
    except Exception as e:
        print("Error downloading", filename, e)
