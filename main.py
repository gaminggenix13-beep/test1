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

# Initialize the generative model
model = genai.GenerativeModel('gemini-1.5-flash')

# Define the exact data structure we expect so Swagger UI creates a text box
class WebhookPayload(BaseModel):
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