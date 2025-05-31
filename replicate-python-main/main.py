import os
import re
import time
import replicate
import requests
from flask import Flask, request, jsonify
from base64 import b64encode

app = Flask(__name__)
client = replicate.Client(api_token=os.environ["REPLICATE_API_TOKEN"])

def upload_to_wordpress(image_path, filename="output.png"):
    wp_url = os.environ["WP_URL"]
    wp_user = os.environ["WP_USER"]
    wp_pass = os.environ["WP_APP_PASS"]
    credentials = f"{wp_user}:{wp_pass}"
    token = b64encode(credentials.encode())

    headers = {
        "Authorization": f"Basic {token.decode()}",
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": "image/png"
    }

    with open(image_path, 'rb') as img:
        response = requests.post(
            f"{wp_url}/wp-json/wp/v2/media",
            headers=headers,
            data=img
        )

    if response.status_code in [200, 201]:
        return response.json()["source_url"]
    else:
        raise Exception(f"Upload failed: {response.status_code} - {response.text}")

@app.route("/generate", methods=["POST"])
def generate_image():
    data = request.json
    prompt = data.get("prompt", "A warm, modern kitchen")
    headline = data.get("headline", "generated-image")

    # Clean and format the headline for a filename
    safe_headline = re.sub(r'[^a-zA-Z0-9_\-]+', '-', headline.lower()).strip('-')
    timestamp = int(time.time())
    filename = f"{safe_headline}-{timestamp}.png"

    output = client.run(
        "fofr/flux-black-light:d0d48e298dcb51118c3f903817c833bba063936637a33ac52a8ffd6a94859af7",
        input={
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "output_format": "png"
        }
    )

    with open("output.png", "wb") as f:
        f.write(output[0].read())

    image_url = upload_to_wordpress("output.png", filename=filename)
    return jsonify({ "image_url": image_url })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
