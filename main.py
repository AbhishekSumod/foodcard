from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import json

# Initialize FastAPI
app = FastAPI()

# Enable CORS (for Flutter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq client
groq_client = Groq(api_key="your_groq_api_key_here")

# Request body schema
class MenuRequest(BaseModel):
    text: str

@app.post("/parse_menu")
async def parse_menu(req: MenuRequest):
    try:
        # Prompt for Groq
        prompt = f"""
        You are a helpful assistant. Analyze the following restaurant menu text
        and extract structured JSON with categories and items.

        Example format:
        [
          {{
            "name": "Starters",
            "items": [
              {{"name": "Paneer Tikka", "price": "120"}},
              {{"name": "Chicken Kebab", "price": "150"}}
            ]
          }},
          {{
            "name": "Drinks",
            "items": [
              {{"name": "Mango Shake", "price": "80"}}
            ]
          }}
        ]

        Menu text:
        {req.text}
        """

        # Call Groq API
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )

        # Extract AI response
        ai_response = completion.choices[0].message.content

        # Try parsing JSON
        try:
            categories = json.loads(ai_response)
        except:
            categories = [{"name": "Menu", "items": [{"name": req.text, "price": ""}]}]

        return {"categories": categories}

    except Exception as e:
        return {"categories": [], "error": str(e)}
