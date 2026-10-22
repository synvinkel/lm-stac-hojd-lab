import json
import requests
import os
from dotenv import load_dotenv
from tqdm import tqdm

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

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Work out which tiles are already complete, so progress and ETA cover the full run
tiles = []
for feature in collection_items_as_json["features"]:
    asset = feature["assets"][ASSET_TYPE]
    asset_url = asset["href"]
    filename = asset_url.split("/")[-1]
    filepath = os.path.join(OUTPUT_DIR, filename)
    expected_size = asset.get("file:size")
    complete = os.path.exists(filepath) and (
        expected_size is None or os.path.getsize(filepath) == expected_size
    )
    tiles.append((asset_url, filename, filepath, expected_size, complete))

total_tiles = len(tiles)
done_tiles = sum(1 for t in tiles if t[4])
failed_tiles = 0
total_bytes = sum(t[3] or 0 for t in tiles)
done_bytes = sum(t[3] or 0 for t in tiles if t[4])

print(
    f"{total_tiles} tiles, {done_tiles} already downloaded, "
    f"{total_tiles - done_tiles} to go"
)

# Overall progress in bytes: shows data done, percentage and ETA for the full
# run. Already downloaded tiles count as done but not toward the rate.
overall = tqdm(
    total=total_bytes,
    initial=done_bytes,
    unit="B",
    unit_scale=True,
    unit_divisor=1024,
    desc="Total",
    position=0,
    dynamic_ncols=True,
)
overall.set_postfix_str(f"tiles {done_tiles}/{total_tiles}")

# Download assets for each item in the collection
for asset_url, filename, filepath, expected_size, complete in tiles:
    if complete:
        continue

    partpath = filepath + ".part"
    written = 0

    # Download asset to a .part file and rename it when complete, so an
    # interrupted download never leaves a file that looks finished
    try:
        with requests.get(asset_url, auth=auth, stream=True) as response:
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            with open(partpath, "wb") as f, tqdm(
                total=expected_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=filename,
                position=1,
                leave=False,
                dynamic_ncols=True,
            ) as tile_bar:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
                    written += len(chunk)
                    tile_bar.update(len(chunk))
                    overall.update(len(chunk))

        if expected_size is not None and os.path.getsize(partpath) != expected_size:
            os.remove(partpath)
            raise Exception("size mismatch")

        os.replace(partpath, filepath)
        done_tiles += 1
    except Exception as e:
        failed_tiles += 1
        overall.update(-written)
        tqdm.write(f"Error downloading {filename} - {e}")

    overall.set_postfix_str(
        f"tiles {done_tiles}/{total_tiles}"
        + (f", {failed_tiles} failed" if failed_tiles else "")
    )

overall.close()
print(f"Done: {done_tiles}/{total_tiles} tiles, {failed_tiles} failed")
