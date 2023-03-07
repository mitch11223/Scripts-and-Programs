import speech_recognition as sr
import os
from playaudio import playaudio
import time
from gtts import gTTS
import pyaudio
import requests
import json
import openai
import pydub
from pydub import AudioSegment


openai.api_key = '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'

def openai_API(prompt):

    # Define the prompt you want to use for generating predictions
    prompt = prompt

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1000,
    )
    
    reply = response.choices[0].text
    #make it smoother by removing '.'
    #reply = reply.replace('.','')
    #reply = reply.replace(',','')
    
    return reply


def speak(text):
    #Generate sppech to text and save to .mp3
    tts = gTTS(text=text, lang='en')
    filename = 'voice.mp3'
    tts.save(filename)
    
    song = AudioSegment.from_mp3(filename)
    
    # remove pauses
    pause_length = 1000 #milliseconds
    result = AudioSegment.silent(duration=500)

    for i in range(len(song)):
        if song[i].dBFS > -40:
            result += song[i]

    # save the result
    result.export(filename, format="mp3")
    
    playaudio(filename)


def get_audio():
    # Create an instance of Recognizer
    r = sr.Recognizer()
    if 'Plantronics Blackwire 5210 Series' in sr.Microphone.list_microphone_names():
        device_ = 2
    elif "Mitchell's AirPods" in sr.Microphone.list_microphone_names():
        device_ = 0
    else:
        device_ = None
    # Get audio input from the microphone
    with sr.Microphone(device_index=device_) as source:
        print("Say something:")
        audio = r.listen(source)
        text = ''
        
        # Use the Recognizer to recognize the audio
        try:
            text = r.recognize_google(audio)
            print("You said: {}".format(text))
        except Exception:
            print("Sorry, I didn't understand that")
    return text


def chatbot(text):
    reply = openai_API(text)
    speak(reply)


while True:
    text = get_audio()
    chatbot(text)
    
