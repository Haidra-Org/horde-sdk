from pydantic import BaseModel


class RequestErrorResponse(BaseModel):
    message: str
