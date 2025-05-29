from pydantic import BaseModel


class Query(BaseModel):
    question: str
    provider: str
    model: str
    temperature: float

    class Config:
        extra = "allow"
