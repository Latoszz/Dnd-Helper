from pydantic import BaseModel, Extra


class Request(BaseModel):
    question: str
    provider: str
    model: str
    temperature: float

    class Config:
        extra = 'allow'
