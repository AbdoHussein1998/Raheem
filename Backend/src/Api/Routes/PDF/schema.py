from pydantic import BaseModel
from fastapi import UploadFile,File
from typing import Optional
from dataclasses import dataclass
from fastapi import Depends, File, Form, UploadFile
from typing import Annotated
class UpladedFile(BaseModel):
    file_id:str
    hashed_name:str
    file_name:str
    object_key:str

@dataclass
class RegisterFile:
    file: Annotated[UploadFile, File()]
    ocr: Annotated[bool, Form()]
    force: Annotated[bool, Form()] = False