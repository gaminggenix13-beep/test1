import os
from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai

# Initialize FastAPI application
app = FastAPI()

# Configure the Gemini API key securely
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Fix: Switched to gemini-pro to resolve the 404 model not found error
model = genai.GenerativeModel('gemini-pro')

# Define the exact data structure for Swagger UI
class WebhookPayload(BaseModel):
    # This is purely a placeholder test prompt. You can change this text to anything.
    prompt: str = "Write a short, high-converting cold email pitching an AI voice receptionist to a dental clinic."

@app.post("/webhook")
async def receive_webhook(payload: WebhookPayload):
    # Generate the artifact using Gemini based on the incoming prompt
    try:
        response = model.generate_content(payload.prompt)
        generated_artifact = response.text
    except Exception as e:
        generated_artifact = f"Error generating artifact: {str(e)}"

    # Return the final product
    return {
        "status": "success",
        "received_data": {"prompt": payload.prompt},
        "artifact": generated_artifact
    }

@app.get("/")
async def root():
    return {"status": "online", "service": "GTM-Artifact Automator"}