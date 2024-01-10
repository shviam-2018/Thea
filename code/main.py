import datetime
import speech_recognition as sr
import pyttsx3
from mood import (happy_list, sad_list, angry_list, depressed_list, suicidal_list, happy_mood_responses, sad_mood_responses, angry_mood_responses, depressed_mood_responses, suicidal_mood_responses, general_responses)

# Initialize the text-to-speech engine
engine = pyttsx3.init()
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[1].id)

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

# Ask for the user's name and start the therapy session and desclaimer that say this is Not a real therapist just a script 
while True:
    speak_and_print("Before we proceed, please note that Thea is an AI therapist designed to provide support and companionship. It is not a substitute for professional mental health care. If you are experiencing severe distress or have suicidal thoughts, please seek immediate help from a mental health professional or contact a helpline in your region.")

    speak_and_print("The Thea development team emphasizes that while Thea aims to be supportive, it is not a licensed therapist. The AI is continually learning and evolving, and your feedback is valuable for its improvement. The Thea team does not take responsibility for any harm caused by the program; use it at your own risk.")

    disclaimer = "If you understand that Thea is not a real therapist and you have read and understood the disclaimer, please type 'thea is not a real therapist and i have read and understood the disclaimer': "

    
    speak_and_print(disclaimer)
    user_agree = input("type hear: ").lower()
    
    if user_agree == "thea is not a real therapist and i have read and understood the disclaimer":
        break  # Break out of the loop if the user agrees
    elif user_agree == "admin code 110308":
        break

# Proceed with the therapy session
speak_and_print("Now, please state your name for easy communication")
name = input("Your Name: ")


print(f"I am Thea, your therapist for today, {name} remember that you can end the session whenever you what by saying `ok, thank you for the session` to . Let's start. How are you feeling today?")
speak(f"I am Thea, your therapist for today, {name} remember that you can end the session whenever you what by saying `ok, thank you for the session` to . Let's start. How are you feeling today")

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

        elif any(word in user_statement for word in suicidal_list):
            suicidal_mood_responses()
            
        elif user_statement == "ok thank you for the session":
            speak_and_print("Ok then see you next time")
            
        if all(word not in user_statement for word in happy_list + sad_list + angry_list + depressed_list + suicidal_list):
            general_responses()
