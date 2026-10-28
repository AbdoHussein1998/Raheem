from pydantic import BaseModel

class UpladedFile(BaseModel):
    file_id:str
    hashed_name:str
    file_name:str
    object_key:str
    