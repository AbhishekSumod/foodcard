from fastapi import FastAPI
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize FastAPI
app = FastAPI()

# Request body schema
class ChatRequest(BaseModel):
    message: str

# Route for chat
@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": req.message}],
        )
        return {"reply": response.choices[0].message["content"]}
    except Exception as e:
        return {"error": str(e)}
