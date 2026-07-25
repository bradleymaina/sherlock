from fastapi import FastAPI
from main import add_lecturer, lecturer_lookup

app = FastAPI()

@app.put("/")
def add_lecturer(first_name: str, last_name: str, phone_number: str):
    return {
        "first_name": first_name,
        "last_name": last_name,
        "phone_number": phone_number
    }
