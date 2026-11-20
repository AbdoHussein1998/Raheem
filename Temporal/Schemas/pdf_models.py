from pydantic import BaseModel


class PDFIndexDownloadRequest(BaseModel):
    document_id: str


class PDFObjectKeyRequest(BaseModel):
    document_id: str
    using_ocr: bool
    bucket_name: str
    object_key: str


class PDFUpdateIndexRequest(BaseModel):
    document_id: str
    registration_status: str
    result_object_key: str

    