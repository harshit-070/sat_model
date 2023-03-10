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
import soundfile
import speech_recognition as sr
import requests
from pydub import AudioSegment
import moviepy.editor
import tempfile
import openai

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


openai.api_key = session_token


@app.post("/chat")
async def chatGPT(request: ChatGPTRequest = Body(...)):
    text = request.text
    completions = openai.Completion.create(
        engine="text-davinci-003",
        prompt=text,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    return {"answer": completions.choices[0].text}


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


class AudioConversionRequest(BaseModel):
    url: str
    target_lang: str
    chatId: str


@app.post("/audio_conversion")
async def audioConversion(request: AudioConversionRequest = Body(...)):
    # Read the audio file using soundfile
    response = requests.get(request.url)
    audio = io.BytesIO(response.content)

    # Initialize the speech recognizer
    r = sr.Recognizer()

    # Convert speech to text
    with sr.AudioFile(audio) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data)

    return {"text": text}


class AudioTextConversionRequest(BaseModel):
    url: str
    target_lang: str
    chatId: str


@app.post("/audio_text")
async def audioConversion(request: AudioTextConversionRequest = Body(...)):
    # Read the audio file using soundfile
    response = requests.get(request.url)
    file_contents = response.content
    audio = AudioSegment.from_file(io.BytesIO(file_contents))
    print(audio)
    wav_data = audio.export(format="wav").read()
    data, samplerate = soundfile.read(io.BytesIO(wav_data))

    # Write the audio data to a new file
    sound_file = f"{request.chatId}.wav"
    soundfile.write(sound_file, data, samplerate, subtype="PCM_16")

    # Transcribe the audio using speech recognition
    r = sr.Recognizer()
    with sr.AudioFile(sound_file) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data)
    tt = GoogleTranslator(source="auto", target=request.target_lang).translate(text)

    # Return the resulting transcription
    return {"transcription": tt}


class VideoAudioConversion(BaseModel):
    url: str
    target_lang: str
    chatId: str


@app.post("/video")
async def audioConversion(request: AudioTextConversionRequest = Body(...)):
    # Read the audio file using soundfile
    # response = requests.get(request.url)
    # file_contents = response.content
    response = requests.get(request.url)
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(response.content)
        temp_filepath = f.name
    video = moviepy.editor.VideoFileClip(temp_filepath)
    audio = video.audio
    audio.write_audiofile(f"./{request.chatId}.wav")
    data, samplerate = soundfile.read(audio.audio_path)

    # Write the audio data to a new file
    sound_file = f"./{request.chatId}.wav"
    soundfile.write(sound_file, data, samplerate, subtype="PCM_16")

    # Transcribe the audio using speech recognition
    r = sr.Recognizer()
    with sr.AudioFile(sound_file) as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data)
    tt = GoogleTranslator(source="auto", target=request.target_lang).translate(text)

    # Return the resulting transcription
    os.remove(temp_filepath)
    return {"transcription": tt}
