import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI , Request
from fastapi.responses import PlainTextResponse 
from pydantic import BaseModel, Field
from typing import  Optional

from .database import add_lecturer , lecturer_lookup
from .conversation import process_message

app = FastAPI()
load_dotenv()


PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")

META_VERIFY_TOKEN = "sherlock_webhook_2026"

class Lecturer(BaseModel):
    first_name: str = Field(
        min_length  = 3,
        max_length = 10,
        pattern=r"^[A-Za-z]+$")
    last_name: str = Field(
        min_length = 3 ,
        max_length = 10,
        pattern=r"^[A-Za-z]+$")
    phone_number: str = Field(
         min_length = 10,
        max_length = 10,
        pattern= r"^(07|01)\d{8}$")

#payload models
class TextMessage(BaseModel):
    body: str

class ButtonReply(BaseModel):
    id: str
    title: str

class ListReply(BaseModel):
    id: str
    title: str

class InteractiveMessage(BaseModel):
    type: str
    button_reply: Optional[ButtonReply] = None
    list_reply: Optional[ListReply] = None

class Message(BaseModel):
    from_number: str = Field(alias="from")
    type: str
    text: Optional[TextMessage] = None
    interactive: Optional[InteractiveMessage] = None

class Value(BaseModel):
    messages: Optional[list[Message]] = None

class Change(BaseModel):
    value: Value


class Entry(BaseModel):
    changes: list[Change]

class WebhookPayload(BaseModel):
    object: Optional[str]
    entry: list[Entry]


@app.post("/lecturers")
def create_lecturer(lecturer: Lecturer):
    result = add_lecturer(
        lecturer.first_name,
        lecturer.last_name,
        lecturer.phone_number
    )
    return result

@app.get("/lecturers/search")
def get_lecturer(search_name:str ):
    result = lecturer_lookup(
        search_name
    )
    return result

@app.get("/webhook")
def verify_webhook(request: Request):

    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe"  and token == META_VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    return PlainTextResponse(
        "Verification failed",
        status_code=403
    ) 

def send_whatsapp_message(wa_id, message):
    url = f"https://graph.facebook.com/v26.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp", 
        "to": wa_id,
        "type": "text",
        "text": {
            "body": message
        }
    }

    response  = requests.post(
        url,
        headers=headers,
        json= payload 
    )

    return response
    

@app.post("/webhook")
async def receive_webhook(payload: WebhookPayload):

    #validate entries and changes
    if not payload.entry or not payload.entry[0].changes:
        return{"status": "ignored"}

    value = payload.entry[0].changes[0].value

    #when there is no message in the payload
    if not value.messages:
        return {"status": "ignored"}

    #incoming messages
    message = value.messages[0]

    if message.type == "text" and message.text:
        wa_id = message.from_number
        msg = message.text.body

        reply_text_message =process_message(wa_id, msg)
        print(f"Replying to {wa_id} with message: {reply_text_message}")

        send_whatsapp_message(wa_id, reply_text_message)
        
        return {"status": "success"}

    return {"status": "ignored", "reason": "non-text message"}