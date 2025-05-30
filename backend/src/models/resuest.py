from pydantic import BaseModel, Extra


class Request(BaseModel):
    question: str
    class Config:
        extra = 'allow'
