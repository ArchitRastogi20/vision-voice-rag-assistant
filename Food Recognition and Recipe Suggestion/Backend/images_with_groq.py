import base64
import os
from groq import Groq
from pydantic import BaseModel
from typing import Literal
import json
import time
import csv
from datetime import datetime

class FoodItems(BaseModel):
    items: list[str]
# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

def log_latency(latency_ms: float):
    """Log latency to a CSV file"""
    # Create directory if it doesn't exist
    log_dir = "benchmark_data"
    os.makedirs(log_dir, exist_ok=True)
    
    filename = os.path.join(log_dir, "food_latency.csv")
    file_exists = os.path.isfile(filename)
    
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['timestamp', 'latency_ms'])
        
        writer.writerow([datetime.utcnow().isoformat(), latency_ms])

def get_items(image_path):
    base64_image = encode_image(image_path)
    client = Groq(api_key=GROQ_API_KEY)

    start_time = time.time()
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Give me a list containing only names of food items in the image?"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "food_items",
                "schema": FoodItems.model_json_schema()
            }
        },
        model="meta-llama/llama-4-scout-17b-16e-instruct",
    )
    end_time = time.time()
    log_latency((end_time - start_time) * 1000)

    review = FoodItems.model_validate(json.loads(chat_completion.choices[0].message.content))
    return review.items