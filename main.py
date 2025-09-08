from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import json
import re
import os

# Initialize FastAPI
app = FastAPI()

# Enable CORS (for Flutter or web client)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq client (read API key from environment variable)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
        ai_response = completion.choices[0].message.content.strip()
        print("Raw AI response:", ai_response)

        # Try to extract JSON block from the response
        json_match = re.search(r"\[.*\]", ai_response, re.DOTALL)

        try:
            if json_match:
                categories = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
        except Exception as parse_err:
            print("Parse error:", parse_err)
            categories = [{"name": "Menu", "items": [{"name": req.text, "price": ""}]}]

        return {"categories": categories}

    except Exception as e:
        return {"categories": [], "error": str(e)}

# Health check endpoint (for Render)
@app.get("/healthz")
def health_check():
    return {"status": "ok"}
