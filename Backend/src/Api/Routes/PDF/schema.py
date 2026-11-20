from pydantic import BaseModel
from fastapi import UploadFile,File
from typing import Optional
class UpladedFile(BaseModel):
    file_id:str
    hashed_name:str
    file_name:str
    object_key:str

class RegisterFile(BaseModel):
    file:UploadFile = File(...)
    ocr:bool=...
    force:Optional[bool]