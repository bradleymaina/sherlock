from fastapi import FastAPI , Request
from fastapi.responses import PlainTextResponse 
from pydantic import BaseModel, Field

from database import add_lecturer , lecturer_lookup
from conversation import process_message

app = FastAPI()

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

@app.post("/webhook")
async def receive_webhook(request: Request):

    data = await request.json()
    print(data)

    type = data["entry"][0]["changes"][0]["value"]["messages"][0]["type"]

    if type == "text":
        wa_id =  data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
    else:
        exit()
        return {
            "status": "error",
            "message": "Must be of type text "
        }

    process_message(wa_id, msg)

    return {"status": "received"}