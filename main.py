from fastapi import FastAPI, Body, Response
from fastapi.responses import StreamingResponse
from typing import List
from pydantic import BaseModel
from deep_translator import GoogleTranslator
from pyChatGPT import ChatGPT
import os
import io
from dotenv import load_dotenv
from gtts import gTTS

load_dotenv()
session_token = os.getenv("CHAT_GPT_SESSION_TOKEN")

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


class ChatGPTRequest(BaseModel):
    text: str


# api = ChatGPT(session_token)


# @app.post("/chat")
# async def chatGPT(request: ChatGPTRequest = Body(...)):
#     text = request.text
#     response = api.send_message(text)
#     return {"answer": response["message"]}


class AudioTranslateRequest(BaseModel):
    text: str
    target_lang: str


@app.post("/audio")
async def translateAudio(request: AudioTranslateRequest = Body(...)):
    text = request.text
    target_langs = request.target_lang
    tt = GoogleTranslator(source="auto", target=target_langs).translate(text)
    at = gTTS(tt)
    audio_file = io.BytesIO()
    at.write_to_fp(audio_file)
    audio_file.seek(0)
    headers = {"Content-Disposition": "attachment; filename=speech.mp3"}
    return StreamingResponse(audio_file, headers=headers, media_type="audio/mpeg")
