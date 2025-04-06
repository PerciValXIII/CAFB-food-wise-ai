from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from typing import List

class ResponseModel(BaseModel):
    message: str
    payload: Optional[dict] = {}

class LoginSchema(BaseModel):
    email: str
    password: str

class SignupSchema(BaseModel):
    name: str
    email: str
    password: str
    role:str

class SearchRequest(BaseModel):
    query: str
    collections: List[str]
    top_n_each: int = 5
    top_n_total: int = 10