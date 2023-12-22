import webbrowser
import datetime
import random
import speech_recognition as sr
import pyttsx3

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

def takecommand():
# it takes microphone input and ruterns string output
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("listening...")
        r.pause_threshold = 1
        audio = r.listen(source)
        
    try: 
        print("recognizing...")
        User_statment = r.recognize_google(audio, language="en-us")
        print(f"userside {User_statment}\n")
        
    except Exception as e:
        print("say that agein please...")
        return "None"
    return User_statment 

def happy_mood_responses():
    responses = [
        "Tell me more. It sound interesting",
        "I am so happy for you!",
        "That's fantastic news!",
        "You're doing great!",
        "I knew you could do it!"
    ]
    speak(random.choice(responses))

def sad_mood_responses():
    responses = [
        "it's ok i know how you may be felling right now",
        "I'm here for you.",
        "It's okay to feel this way.",
        "Let's work through it together.",
        "Take your time, I'm listening."
    ]
    speak(random.choice(responses))
    
def angry_mood_responses():
    responses = [
        "I understand you're angry right now.",
        "It's okay to feel angry; let's talk about it.",
        "I'm here to support you, even when you're angry.",
        "Let's find a way to channel that anger into something positive.",
        "Take a deep breath; we can work through this together."
    ]
    speak(random.choice(responses))

def depressed_mood_responses():
    responses = [
        "I'm sorry you're feeling this way.",
        "You don't have to go through it alone; I'm here for you.",
        "Let's take things one step at a time.",
        "It's okay to ask for help; I'm here to support you.",
        "Remember, you're not alone in this."
    ]
    speak(random.choice(responses))


# Add more mood functions like angry_mood_responses(), depressed_mood_responses(), etc.

if __name__ == "__main__":
    wishme()
    while True:
        User_statment = takecommand().lower()

        if "happy" in User_statment:
            happy_mood_responses()
        elif "sad" in User_statment:
            sad_mood_responses()
        # Add more conditions for other moods

        elif "youtube" in User_statment:
            webbrowser.open("youtube.com")
        else:
            print("I can't answer you. I'm sorry.")
            speak("I can't answer you. I'm sorry.")
