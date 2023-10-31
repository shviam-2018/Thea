import os
import pyaudio
import time
import playground 
from gtts import gTTS
import openai
import speech_recognition as sr
import env

name = input("name you terapist: ")

api_key = env(api_key)

lang = 'en'

openai.api_key = api_key

while True:
    def get_audio():
        r = sr.Recognizer()
        with sr.Microphone() as source:
            audio = r.listen(source)
            said = ""
            
            try:
                said = r.recognize_google(audio)
                print(said)
                
                if name in said:
                    chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": said}])