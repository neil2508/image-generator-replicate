import os
import re
import replicate
import requests
from flask import Flask, request, jsonify
from base64 import b64encode

app = Flask(__name__)
@app.route("/", methods=["GET"])
def home():
    return "✅ Your app is running."

# Set up Replicate client
client = replicate.Client(api_token=os.environ["REPLICATE_API_TOKEN"])

# Utility to slugify the headline for a safe filename
def slugify(text):
    return re.sub(r'[-\s]+', '-', re.sub(r'[^\w\s-]', '', text.lower())).strip('-_')

# Upload to WordPress
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
        media = response.json()
        return {
            "source_url": media["source_url"],
            "id": media["id"]
        }
    else:
        raise Exception(f"Upload failed: {response.status_code} - {response.text}")

# Main image generation endpoint
@app.route("/generate", methods=["POST"])
def generate_image():
    data = request.json
    prompt = data.get("prompt", "A modern eco kitchen with natural textures")
    headline = data.get("headline", "output")
    filename = f"{slugify(headline)}.png"

    output = client.run(
        "fofr/flux-black-light:d0d48e298dcb51118c3f903817c833bba063936637a33ac52a8ffd6a94859af7",
        input={
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "output_format": "png"
        }
    )

    # Save image locally
    with open(filename, "wb") as f:
        f.write(output[0].read())

    # Upload to WordPress
    media_data = upload_to_wordpress(filename, filename=filename)

    return jsonify({
        "image_url": media_data["source_url"],
        "image_id": media_data["id"]
    })

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
