import os
import asyncio
import httpx
from fastapi import FastAPI, Request, BackgroundTasks
import google.generativeai as genai

app = FastAPI()

# 1. Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Switched to gemini-pro to fix the 404 API version error
model = genai.GenerativeModel('gemini-pro')

# 2. Make.com Webhook URL
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

async def process_pr_and_notify(pr_data: dict):
    """Background task to avoid GitHub timeouts and rate limits."""
    await asyncio.sleep(2)

    pr_title = pr_data.get("title", "No title")
    pr_body = pr_data.get("body", "No description provided")
    pr_author = pr_data.get("user", {}).get("login", "Unknown author")
    repo_name = pr_data.get("head", {}).get("repo", {}).get("name", "Repository")

    # Updated prompt to exactly match your old message structure and tone
    prompt = f"""
    You are an expert DevRel and Product Marketer. A pull request was just merged into the repo '{repo_name}'.
    
    PR Title: {pr_title}
    Author: {pr_author}
    Description/Diff Context: {pr_body}

    Based on this, generate exactly 4 release artifacts. You MUST use the exact formatting and emojis below:

    📢 Changelog Entry:
    [Write the user-facing changelog here in an exciting tone]

    💼 LinkedIn Post:
    [Write the LinkedIn post here]

    🐦 Twitter Post:
    [Write the short Twitter post here]

    💬 Internal Slack Summary:
    [Write the team summary here]
    """

    try:
        response = model.generate_content(prompt)
        generated_text = response.text
    except Exception as e:
        generated_text = f"Error generating artifact: {str(e)}"

    if MAKE_WEBHOOK_URL:
        payload_to_make = {
            "repository": repo_name,
            "pr_title": pr_title,
            "author": pr_author,
            "gtm_artifact": generated_text
        }
        try:
            async with httpx.AsyncClient() as client:
                await client.post(MAKE_WEBHOOK_URL, json=payload_to_make, timeout=10.0)
        except Exception as e:
            print(f"Failed to push to Make.com: {e}")

async def process_regeneration(payload: dict):
    """Background task to rewrite existing drafts."""
    original_text = payload.get("original_text", "")
    if not original_text:
        return

    # Forcing the AI to keep your exact structural layout during regeneration
    prompt = f"""
    You are an expert DevRel and Product Marketer. 
    The client requested a revision of the following release drafts. 
    Please rewrite them to be fresher and slightly different. 
    You MUST maintain the exact same 4-part structure and emojis:

    📢 Changelog Entry:
    ...
    💼 LinkedIn Post:
    ...
    🐦 Twitter Post:
    ...
    💬 Internal Slack Summary:
    ...
    
    Original Drafts to Rewrite:
    {original_text}
    """

    try:
        response = model.generate_content(prompt)
        generated_text = response.text
    except Exception as e:
        generated_text = f"Error regenerating artifact: {str(e)}"

    if MAKE_WEBHOOK_URL:
        payload_to_make = {
            "repository": "Regenerated Draft",
            "pr_title": "AI Revision",
            "author": "GTM Automator",
            "gtm_artifact": generated_text
        }
        try:
            async with httpx.AsyncClient() as client:
                await client.post(MAKE_WEBHOOK_URL, json=payload_to_make, timeout=10.0)
        except Exception as e:
            print(f"Failed to push regeneration to Make.com: {e}")

@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    event_type = request.headers.get("X-GitHub-Event")
    payload = await request.json()

    if "prompt" in payload:
        try:
            res = model.generate_content(payload["prompt"])
            return {"status": "success", "artifact": res.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    if event_type == "pull_request":
        action = payload.get("action")
        is_merged = payload.get("pull_request", {}).get("merged", False)

        if action == "closed" and is_merged:
            pr_data = payload.get("pull_request", {})
            background_tasks.add_task(process_pr_and_notify, pr_data)
            return {"status": "accepted", "message": "PR is merged. Processing GTM artifact in background."}
        else:
            return {"status": "ignored", "message": f"PR action '{action}' (merged={is_merged}) ignored."}

    return {"status": "ignored", "message": f"Event '{event_type}' ignored to save resources."}

@app.post("/regenerate")
async def regenerate_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    background_tasks.add_task(process_regeneration, payload)
    return {"status": "accepted", "message": "Regenerating artifact in background."}

@app.get("/")
async def root():
    return {"status": "online", "service": "GTM-Artifact Automator"}