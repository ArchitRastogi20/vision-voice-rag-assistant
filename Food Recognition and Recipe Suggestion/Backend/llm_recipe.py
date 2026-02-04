import os

# Get API key from environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

from groq import Groq
client = Groq(api_key=GROQ_API_KEY)
def llm_recipe(ingredients_list, cuisine_name=[]):
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": f"Give one detailed recipe including preparation time for each cuisine in give in the cuisine {cuisine_name} using  these ingredients{ingredients_list} ,if no cusine is provided you are free to choose on your own and  if the recipe is not possible just say \"I can't make a recipe out of these ingredients and never give a blank response,\"\n"
            },
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )
    
    response = ""
    for chunk in completion:
        response += chunk.choices[0].delta.content or ""
    return response

def masterchef(query, cuisine, result, item):
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": f"Suppose in your last message you sent me :{result} as a response to my query , which was to suggest recipe from {cuisine} cuisines using the items : {item} and regarding the same conversation I have another query :{query}, please answer this only in the context of the things i mentioned"
            },
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )
    feedback = ""
    for chunk in completion:
        feedback += chunk.choices[0].delta.content or ""
    return feedback