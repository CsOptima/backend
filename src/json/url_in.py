from openai import BaseModel


class UrlIn(BaseModel):
    url: str