import os
from fastapi import FastAPI, Request
import google.generativeai as genai

# Initialize FastAPI application
app = FastAPI()

# Configure the Gemini API key securely
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Initialize the generative model
model = genai.GenerativeModel('gemini-1.5-flash')

@app.post("/webhook")
async def receive_webhook(request: Request):
    # 1. Parse the incoming data
    try:
        payload = await request.json()
        # Extract the specific instruction from the payload
        user_prompt = payload.get("prompt", "Write a 1-sentence value proposition for an AI automation agency.")
    except Exception:
        payload = {}
        user_prompt = "Write a 1-sentence value proposition for an AI automation agency."

    # 2. Generate the artifact using Gemini
    try:
        response = model.generate_content(user_prompt)
        generated_artifact = response.text
    except Exception as e:
        generated_artifact = f"Error generating artifact: {str(e)}"

    # 3. Return the final product
    return {
        "status": "success",
        "received_data": payload,
        "artifact": generated_artifact
    }

@app.get("/")
async def root():
    return {"status": "online", "service": "GTM-Artifact Automator"}