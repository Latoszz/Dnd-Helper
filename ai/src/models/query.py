from pydantic import BaseModel


class Query(BaseModel):
    question: str
    model: str
    temperature: float
