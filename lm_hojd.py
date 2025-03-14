import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# ASSET_TYPE = "thumbnail"
ASSET_TYPE = "data"

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

collections_endpoint = create_endpoint_url(base_url, "/collections")
collection_items_endpoint = create_endpoint_url(
    base_url, "/collections/{collection_id}/items?limit={limit}"
)
### End swagger setup

# Get available collections
collections_response = requests.get(collections_endpoint, auth=auth)
collections_as_json = collections_response.json()

# Download assets for each collection
for collection in collections_as_json["collections"]:
    collection_id = collection["id"]

    collection_items_response = requests.get(
        collection_items_endpoint.format(collection_id=collection_id, limit=10000),
        auth=auth,
    )
    collection_items_as_json = collection_items_response.json()

    # Download assets for each item in the collection
    for feature in collection_items_as_json["features"]:
        asset_url = feature["assets"][ASSET_TYPE]["href"]
        filename = asset_url.split("/")[-1]
        filepath = os.path.join("assets", filename)

        os.makedirs("assets", exist_ok=True)

        # Skip if file already exists
        if os.path.exists(filepath):
            print("Skipping", filename, "- already exists")
            continue

        # Download asset
        print("Downloading", filename)
        try:
            response = requests.get(asset_url, auth=auth)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                    print("Done downloading", filename)
            else:
                print(f"Error downloading {filename} - HTTP {response.status_code}")
        except Exception as e:
            print("Error downloading", filename, e)
