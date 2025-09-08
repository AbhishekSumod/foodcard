from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import openai
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize FastAPI
app = FastAPI()

# Allow Flutter app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Root route -----------------
@app.get("/")
async def root():
    return {"message": "Menu Parser API is running!"}

# ----------------- MenuText Schema -----------------
class MenuText(BaseModel):
    text: str

# ----------------- Menu Parser using OpenAI -----------------
@app.post("/parse_menu")
async def parse_menu_ai(data: MenuText):
    prompt = f"""
You are an AI menu parser. Analyze the following restaurant menu text.
Return a JSON array of categories. Each category must have a 'name' and an 'items' array.
Each item must have 'name' and 'price' fields.

Format example:
[
  {{
    "name": "Drinks",
    "items": [
      {{"name": "Lemon Soda", "price": "$2"}},
      {{"name": "Mango Shake", "price": "$3"}}
    ]
  }},
  {{
    "name": "Fast Food",
    "items": [
      {{"name": "Cheese Burger", "price": "$5"}}
    ]
  }}
]

Menu Text:
{data.text}
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        content = response.choices[0].message["content"]

        # Try to parse AI response as JSON
        try:
            categories = json.loads(content)
        except Exception as e:
            print("❌ JSON parsing failed:", e)
            categories = []

        return {"categories": categories}

    except Exception as e:
        print("❌ OpenAI error:", e)
        return {"categories": []}
