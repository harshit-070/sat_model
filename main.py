from fastapi import FastAPI, Body
from typing import List
from pydantic import BaseModel
from deep_translator import GoogleTranslator

app = FastAPI()


@app.get("/")
def index():
    return {"message": "ok"}


class TranslationRequest(BaseModel):
    text: str
    target_langs: str


@app.post("/translate")
async def translate_text(request: TranslationRequest = Body(...)):
    text = request.text
    target_langs = request.target_langs
    tt = GoogleTranslator(source="auto", target=target_langs).translate(text)
    return {"translate_text": tt}
