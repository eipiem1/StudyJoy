import os
import requests
import json
import argparse
from PIL import Image
from io import BytesIO

def generate_image(prompt):
    model = os.getenv("OPENAI_API_VLM_MODEL", "black-forest-labs/FLUX.1-schnell")
    base_url = os.getenv("OPENAI_API_BASE", "https://api.siliconflow.cn/v1")
    url = f"{base_url}/images/generations"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "prompt": prompt,
        "image_size": "768x512",
        "batch_size": 1,
        "seed": 4999999999,
        "num_inference_steps": 20,
        "guidance_scale": 7.5,
        "prompt_enhancement": True
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_json = response.json()
    image_url = response_json["images"][0]["url"]
    return image_url

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an image from a prompt.")
    parser.add_argument("PROMPT", type=str, help="The prompt to generate the image from.")
    args = parser.parse_args()
    prompt = args.PROMPT
    image_url = generate_image(prompt)
    if image_url:
        response = requests.get(image_url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            image.show()
        else:
            print("Failed to retrieve image")
    else:
        print("Failed to generate image URL")
