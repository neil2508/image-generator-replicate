from flask import Flask, request, jsonify
import replicate
import base64
import requests

app = Flask(__name__)

@app.route("/generate-image", methods=["POST"])
def generate_image():
    data = request.json
    prompt = data.get("prompt")
    post_title = data.get("post_title")

    if not prompt or not post_title:
        return jsonify({"error": "Missing 'prompt' or 'post_title' in request body"}), 400

    try:
        output = replicate.run(
            "stability-ai/sdxl:3e45b18b5c57b3d7e6d2db9b3e9459b745e8594b11e34ec98d70e740af57eb2c",
            input={
                "prompt": prompt,
                "width": 1024,
                "height": 576
            }
        )
        image_url = output[0]

        # Fetch image and convert to base64
        image_data = requests.get(image_url).content
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        return jsonify({
            "image_url": image_url,
            "image_base64": image_base64,
            "image_name": f"{post_title.replace(' ', '_').lower()}.png"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

