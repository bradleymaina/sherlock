from fastapi import FastAPI  
from pydantic import BaseModel

from main import add_lecturer , lecturer_lookup


class Lecturer(BaseModel):
    first_name: str
    last_name: str
    phone_number: str

    app = FastAPI()

    @app.post("/lecturers")
    def create_lecturer(first_name: str, last_name: str, phone_number: str):
        result = add_lecturer(
            first_name,
            last_name,
            phone_number
        )
        return result

    @app.get("/lecturers/search")
    def get_lecturer(search_name: str):
        result = lecturer_lookup(
            search_name
        )
        return result