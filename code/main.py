import datetime
import speech_recognition as sr
import pyttsx3
from mood import happy_list, sad_list, angry_list, depressed_list, happy_mood_responses, sad_mood_responses, angry_mood_responses, depressed_mood_responses, general_response

# Initialize the text-to-speech engine
engine = pyttsx3.init("sapi5")
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)

# Function to speak the given audio
def speak(audio):
    engine.say(audio)
    engine.runAndWait()

# Function to greet the user based on the time of day
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

# Call the wishme function to greet the user
wishme()

# Function to print a message and speak it
def speak_and_print(message):
    print(message)
    speak(message)

# Ask for the user's name and start the therapy session
speak_and_print("Before we start today, please state your name for easy communication")
name = input("Your Name: ")
print(name)

print(f"I am Thea, your therapist for today, {name}. Let's start. How are you feeling today?")
speak(f"I am Thea, your therapist for today, {name}. Let's start. How are you feeling today?")

# Function to take microphone input and return string output
def takecommand():    
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

# Main program execution
if __name__ == "__main__":
    while True:
        user_statement = takecommand().lower()

        # Check user's statement against mood lists and provide responses
        if any(word in user_statement for word in happy_list):
            happy_mood_responses()

        if any(word in user_statement for word in sad_list):
            sad_mood_responses()

        elif any(word in user_statement for word in angry_list):
            angry_mood_responses()

        elif any(word in user_statement for word in depressed_list):
            depressed_mood_responses()

        else:
            general_response()
