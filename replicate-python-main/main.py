import os
import replicate
import requests
from flask import Flask, request, jsonify
from base64 import b64encode

app = Flask(__name__)
client = replicate.Client(api_token=os.environ["REPLICATE_API_TOKEN"])

def upload_to_wordpress(image_path, filename="output.webp"):
    wp_url = os.environ["WP_URL"]
    wp_user = os.environ["WP_USER"]
    wp_pass = os.environ["WP_APP_PASS"]
    credentials = f"{wp_user}:{wp_pass}"
    token = b64encode(credentials.encode())

    headers = {
        "Authorization": f"Basic {token.decode()}",
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": "image/webp"
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
    try:
        data = request.json
        prompt = data.get("prompt", "A warm, modern kitchen with natural light")

        # Call Replicate model
        output = client.run(
            "black-forest-labs/flux-1.1-pro",
            input={
                "prompt": prompt,
                "aspect_ratio": "16:9",
                "output_format": "webp",
                "output_quality": 80,
                "safety_tolerance": 2,
                "prompt_upsampling": True
            }
        )

        image_url = output[0]
        image_response = requests.get(image_url)

        with open("output.webp", "wb") as f:
            f.write(image_response.content)

        final_url = upload_to_wordpress("output.webp", filename="output.webp")
        return jsonify({ "image_url": final_url })

    except Exception as e:
        return jsonify({ "error": str(e) }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
