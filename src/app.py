import os
from fastapi import FastAPI, Request
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from dotenv import load_dotenv

import os


# Load environment variables from .env file
load_dotenv(override=True)

# Initialize FastAPI app
app = FastAPI()

# Define a simple root endpoint to check if the app is running


@app.get("/")
async def root():
    return {"status": "app is running"}

# Define the webhook endpoint to receive Jira ticket data


@app.post("/webhook")
async def webhook(request: Request):
    json_payload = await request.json()
    changelog_map = {item["field"]: item["toString"]
                     for item in json_payload["changelog"]["items"]}
    issue_id = json_payload["issue"]["id"]
    issue_key = json_payload["issue"]["key"]
    summary = changelog_map.get("summary")
    description = changelog_map.get("description")
    workflow_payload = f"IssueID: {issue_id}\nIssueKey: {issue_key}\nSummary: {summary}\nDescription: {description}"
    call_classification_workflow(workflow_payload)
    return {"status": "classification workflow triggered"}


def call_classification_workflow(payload: str):

    project_client = AIProjectClient(
        endpoint=os.getenv("AI_PROJECT_ENDPOINT"),
        credential=DefaultAzureCredential(),
    )

    with project_client:

        workflow = {
            "name": os.getenv("WORKFLOW_NAME"),
            "version": os.getenv("WORKFLOW_VERSION"),
        }

        openai_client = project_client.get_openai_client()

        conversation = openai_client.conversations.create()
        print(f"Created conversation (id: {conversation.id})")

        stream = openai_client.responses.create(
            conversation=conversation.id,
            extra_body={"agent_reference": {
                "name": workflow["name"], "type": "agent_reference"}},
            input=str(payload),
            stream=True,
            metadata={"x-ms-debug-mode-enabled": "1"},
        )

        for event in stream:
            print(f"Received event: {event.type}")

            if (event.type == "response.completed"):
                for item in event.response.output:
                    if item.type == "message":
                        for content in item.content:
                            if content.type == "output_text":
                                print(content.text)

        openai_client.conversations.delete(conversation_id=conversation.id)
        print("Conversation deleted")
