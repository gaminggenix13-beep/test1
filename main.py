import os
from fastapi import FastAPI, Request
import google.generativeai as genai

# Initialize FastAPI application
app = FastAPI()

# Configure the Gemini API key securely from Render environment variables
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

@app.post("/webhook")
async def receive_webhook(request: Request):
    # Safely handle incoming payloads, including empty requests from Swagger UI
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    # Placeholder logic for your GTM-artifact generation
    return {
        "status": "success",
        "message": "Webhook processed successfully",
        "received_data": payload
    }

@app.get("/")
async def root():
    return {"status": "online", "service": "GTM-Artifact Automator"}