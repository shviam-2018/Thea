import pyttsx3
import speech_recognition as sr
import datetime
import webbrowser
import random

engine = pyttsx3.init("sapi5")
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)

def speak(audio):
    engine.say(audio)
    engine.runAndWait()

def wishme():
    hour = int(datetime.datetime.now().hour)
    if 0 <= hour < 12:
        speak("Good morning!")
    elif 12 <= hour < 18:
        speak("Good afternoon!")
    else:
        speak("Good evening!")

    speak("I am Campa sir. Please tell me how can I assist you today.")

def happy_mood_responses():
    responses = [
        "I am so happy for you!",
        "That's fantastic news!",
        "You're doing great!",
        "I knew you could do it!"
    ]
    speak(random.choice(responses))

def sad_mood_responses():
    responses = [
        "I'm here for you.",
        "It's okay to feel this way.",
        "Let's work through it together.",
        "Take your time, I'm listening."
    ]
    speak(random.choice(responses))

# Add more mood functions like angry_mood_responses(), depressed_mood_responses(), etc.

if __name__ == "__main__":
    wishme()
    while True:
        query = takecommand().lower()

        if "happy" in query:
            happy_mood_responses()
        elif "sad" in query:
            sad_mood_responses()
        # Add more conditions for other moods

        elif "youtube" in query:
            webbrowser.open("youtube.com")
        else:
            print("I can't answer you. I'm sorry.")
            speak("I can't answer you. I'm sorry.")
