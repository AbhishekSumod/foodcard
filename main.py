from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import json
import re
import os

# Initialize FastAPI
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq client (API key from Render env)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Request body schema
class MenuRequest(BaseModel):
    text: str

@app.post("/parse_menu")
async def parse_menu(req: MenuRequest):
    try:
        # Strict JSON prompt
        prompt = f"""
        You are a helpful assistant. 
        Extract the following restaurant menu text into ONLY valid JSON.
        Do NOT add explanations, comments, or markdown.
        Just return the JSON array.

        Example:
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

        # Groq request
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=800,
        )

        # Raw AI output
        ai_response = completion.choices[0].message.content.strip()
        print("Raw AI response:", ai_response)

        # Try to load JSON directly
        try:
            categories = json.loads(ai_response)
        except:
            # Fallback: extract JSON block with regex
            json_match = re.search(r"\[.*\]", ai_response, re.DOTALL)
            if json_match:
                categories = json.loads(json_match.group())
            else:
                categories = [{"name": "Menu", "items": [{"name": req.text, "price": ""}]}]

        return {"categories": categories}

    except Exception as e:
        return {"categories": [], "error": str(e)}

# Health check
@app.get("/healthz")
def health_check():
    return {"status": "ok"}
