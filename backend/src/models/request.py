from pydantic import BaseModel


class Request(BaseModel):
    question: str
    provider: str
    model: str
    temperature: float

    class Config:
        extra = "allow"
        extra = "allow"
