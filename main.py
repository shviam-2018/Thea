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
        print("Good morning!")
        speak("Good morning!")
    elif 12 <= hour < 18:
        print("Good afternoon")
        speak("Good afternoon!")
    else:
        print("Good evening!")
        speak("Good evening!")

speak("Before we start today please stat you name for easy commiucation")
name = input("Before we start today please stat you name for easy commiucation: ")
print(name)

print(f"I am Thea, your therapist for today, {name}. Let's start. How are you feeling today?")
speak(f"I am Thea, your therapist for today, {name}. Let's start. How are you feeling today?")


def takecommand():
    # It takes microphone input and returns string output
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source)

    try:
        print("Recognizing...")
        user_statement = r.recognize_google(audio, language="en-us")
        print(f"User side: {user_statement}\n")

    except Exception as e:
        print("Say that again, please...")
        return "None"
    return user_statement

def happy_mood_responses():
    responses = [
        "Tell me more. It sounds interesting.",
        "I am so happy for you!",
        "That's fantastic news!",
        "You're doing great!",
        "I knew you could do it!"
    ]
    response = random.choice(responses)
    print(f"Thea: {response}")
    speak(response)

def sad_mood_responses():
    responses = [
        "It's ok; I know how you may be feeling right now.",
        "I'm here for you.",
        "It's okay to feel this way.",
        "Let's work through it together.",
        "Take your time; I'm listening."
    ]
    response = random.choice(responses)
    print(f"Thea: {response}")
    speak(response)

def angry_mood_responses():
    responses = [
        "I understand you're angry right now.",
        "It's okay to feel angry; let's talk about it.",
        "I'm here to support you, even when you're angry.",
        "Let's find a way to channel that anger into something positive.",
        "Take a deep breath; we can work through this together."
    ]
    response = random.choice(responses)
    print(f"Thea: {response}")
    speak(response)

def depressed_mood_responses():
    responses = [
        "I'm sorry you're feeling this way.",
        "You don't have to go through it alone; I'm here for you.",
        "Let's take things one step at a time.",
        "It's okay to ask for help; I'm here to support you.",
        "Remember, you're not alone in this."
    ]
    response = random.choice(responses)
    print(f"Thea: {response}")
    speak(response)


if __name__ == "__main__":
    wishme()
    while True:
        user_statement = takecommand().lower()

        if "happy" in user_statement:
            happy_mood_responses()

        elif "sad" in user_statement:
            sad_mood_responses()

        elif "angry" in user_statement:
            angry_mood_responses()

        elif "depressed" in user_statement:
            depressed_mood_responses()

        else:
            print("I can't answer you. I'm sorry.")
            speak("I can't answer you. I'm sorry.")
