from groq import Groq
import json
import re
import jsonschema
from jsonschema import validate
import os

# Get API key from environment variable (don't hardcode it)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

# Initialize client
client = Groq(api_key=GROQ_API_KEY)

# JSON Schema for validation
recipe_schema = {
    "type": "object",
    "properties": {
        "recipes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "ingredients": {"type": "array", "items": {"type": "string"}},
                    "instructions": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["name", "ingredients", "instructions"]
            }
        }
    },
    "required": ["recipes"]
}

# Function to validate JSON
def validate_recipe_response(json_data, expected_number_of_recipes):
    try:
        validate(instance=json_data, schema=recipe_schema)
        if len(json_data['recipes']) < expected_number_of_recipes:
            print(f"Invalid JSON: Not enough recipes ({len(json_data['recipes'])}/{expected_number_of_recipes})")
            return False
        print("Valid JSON")
        return True
    except jsonschema.exceptions.ValidationError as err:
        print("Invalid JSON:", err)
        return False

# Function to extract JSON from the response
def extract_json_from_response(response_text):
    match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if match:
        return match.group(0)
    else:
        return None

# LLM Recipe function with retry logic
def llm_recipe(number_of_recipes, ingredients_list, cuisine_name='', max_retries=5):
    prompt = f"""
    You are a culinary assistant specializing in recipe generation. Given a number of recipes and a list of ingredients, provide at least {number_of_recipes} detailed recipes in proper JSON format.

    Expected JSON schema:
    {{
        "recipes": [
            {{
                "name": "Recipe Name",
                "description": "Recipe description",
                "ingredients": [
                    "ingredient1",
                    "ingredient2"
                ],
                "instructions": [
                    "step1",
                    "step2"
                ]
            }},
            ...
        ]
    }}

    Input:
    Ingredients: {ingredients_list}
    Cuisine: {cuisine_name if cuisine_name else "any cuisine"}

    Only return the JSON response in the specified format without any additional commentary.
    """

    for attempt in range(max_retries):
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False
        )

        response = completion.choices[0].message.content
        #print(f"Raw Response (Attempt {attempt + 1}):", response)

        json_str = extract_json_from_response(response)
        if json_str:
            try:
                json_response = json.loads(json_str)
                if validate_recipe_response(json_response, number_of_recipes):
                    return json_response
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")

    return {"error": "could not find any recipe"}

# Save JSON data to a JavaScript file
def save_json_to_js(response, js_file='./Frontend/static/js/recipes.js'):
    with open(js_file, 'w') as f:
        f.write(f"const recipes = {json.dumps(response, indent=4)};")

# Generate recipes and save to JS file
#response = llm_recipe(3, ["carrot", "garlic", "eggplant"])
#save_json_to_js(response, 'recipes.js')