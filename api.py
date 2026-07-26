from fastapi import FastAPI  
from pydantic import BaseModel, Field

from main import add_lecturer , lecturer_lookup

app = FastAPI()


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