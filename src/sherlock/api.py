import os
import httpx
import time
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI , Request
from fastapi.responses import PlainTextResponse 
from pydantic import BaseModel, Field
from typing import  Optional
from contextlib import asynccontextmanager

from .database import add_lecturer , lecturer_lookup
from .conversation import process_message

load_dotenv()

client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client

    client = httpx.AsyncClient()

    yield

    await client.aclose()


app = FastAPI(lifespan = lifespan)

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


class ContactName(BaseModel):
    formatted_name: str


class ContactPhone(BaseModel):
    phone: str
    wa_id: Optional[str] = None
    type: Optional[str] = None


class Contact(BaseModel):
    name: ContactName
    phones: list[ContactPhone]


class Message(BaseModel):
    id: str
    from_number: str = Field(alias="from")
    type: str
    text: Optional[TextMessage] = None
    interactive: Optional[InteractiveMessage] = None
    contacts: Optional[list[Contact]] = None


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

async def send_whatsapp_message(wa_id, message, message_id):
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
        },
        "context": {
            "message_id": message_id
        }
    }

    response  = await client.post(
        url,
        headers=headers,
        json= payload 
    )

    return response

async def send_whatsapp_list(wa_id, body, button_title, rows):
    url = f"https://graph.facebook.com/v26.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": wa_id,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {
                "text": body
            },
            "action": {
                "button": button_title,
                "sections": [
                    {
                        "rows": rows
                    }
                ]
            }
        }
    }

    response = await client.post(
        url,
        headers=headers,
        json=payload
    )

    return response

rows = [
    {
        "id": "add_lecturer",
        "title": "Add Lecturer",
        "description": "Add lecturer by providing first name, last name and phone number"
    },
    {
        "id": "search_lecturer",
        "title": "Search Lecturer",
        "description": "search by either first name or last name"
    }
]

async def format_reply(message_id):
    url = f"https://graph.facebook.com/v26.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
        "typing_indicator": {
            "type": "text"
        }
    }

    response = await client.post(
        url,
        headers=headers,
        json=payload
    )

    return response

async def send_lecturer_contacts(wa_id, result):
    url = f"https://graph.facebook.com/v26.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": wa_id,
        "type": "contacts",
        "contacts": result
    }

    
    response = await client.post(
        url,
        headers=headers,
        json=payload
    )
   #  print("CONTACT STATUS:", response.status_code)
   # print("CONTACT RESPONSE:", response.json())
   # print("CONTACT PAYLOAD:", payload)

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

    start = time.perf_counter()

    asyncio.create_task(format_reply(message.id))

    if message.type == "text" and message.text:
        wa_id = message.from_number
        msg = message.text.body

        start = time.perf_counter()

        responses = process_message(wa_id, msg)

         # print(
         #   f"process message: {(time.perf_counter() - start ) * 1000 :2f} ms"
         # )

        for response in responses:
            if response["type"] == "text":

                start = time.perf_counter()

                await send_whatsapp_message(
                    wa_id,
                    response["body"],
                    message.id
                )   

               # print(
               #     f"send message: {(time.perf_counter() - start) * 1000 :2f} ms"
               # )
            elif response["type"] == "list":

                start = time.perf_counter()

                await send_whatsapp_list(
                    wa_id,
                    response["body"],
                    response["button_title"],
                    response["rows"]
                )

                 #print(
                 #   f"sending list: {(time.perf_counter() - start) * 1000:2f} ms"
                 # )

            elif response["type"] == "contacts":

                start = time.perf_counter()

                await send_lecturer_contacts(
                    wa_id,
                    response["data"]
                )

                # print(
                #    f"contact message: {(time.perf_counter() - start) * 1000 :2f} ms"
                #)
        
        return {"status": "success"}

    elif message.type == "interactive" and message.interactive:
        wa_id = message.from_number
        interactive = message.interactive

        if interactive.type == "button_reply" and interactive.button_reply:
            input_value = interactive.button_reply.id

        elif interactive.type == "list_reply" and interactive.list_reply:
            input_value = interactive.list_reply.id

        else:
            return {"status": "ignored", "reason": "unsupported interactive type"}

        start = time.perf_counter()

        responses = process_message(wa_id, input_value)

       # print(
       #    f"interactive process message:"
       #    f"{(time.perf_counter() - start )*1000:2f} ms"
       # )

        for response in responses:
            if response["type"] == "text":

               # print("CONTACT RESPONSE FROM CONVERSATION:", response)

                start = time.perf_counter()

                await send_whatsapp_message(
                    wa_id,
                    response["body"],
                    message.id
                )

               # print(
               #    f"interactive send message:"
               #     f"{(time.perf_counter() - start)*1000:2f} ms"
               #)

            elif response["type"] == "list":

                start = time.perf_counter()

                await send_whatsapp_list(
                    wa_id,
                    response["body"],
                    response["button_title"],
                    response["rows"]
                )

                #print(
                #    f"interactive send list"
                #    f"{(time.perf_counter() - start ) * 1000:2f}ms"
                #)

            elif response["type"] == "contacts":

                start = time.perf_counter()

                await send_lecturer_contacts(
                    wa_id,
                    response["data"]
                )

               # print(
               #    f"interactive send contacts"
               #    f"{(time.perf_counter() - start) * 1000:2f} ms"
               # )
                
        return {"status": "success"}
    
    return {"status": "ignored", "reason": "non-text message"}