import datetime
import speech_recognition as sr
import pyttsx3
from mood import (happy_list, sad_list, angry_list, depressed_list, suicidal_list, happy_mood_responses, sad_mood_responses, angry_mood_responses, depressed_mood_responses, suicidal_mood_responses, general_responses)
from functions import (wishme, takecommand, speak_and_print, speak)

# Initialize the text-to-speech engine
engine = pyttsx3.init()
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[1].id)

# Call the wishme function to greet the user
wishme()

# Ask for the user's name and start the therapy session and desclaimer that say this is Not a real therapist just a script 
while True:
    speak_and_print("Before we proceed, please note that Thea is an AI therapist designed to provide support and companionship. It is not a substitute for professional mental health care. If you are experiencing severe distress or have suicidal thoughts, please seek immediate help from a mental health professional or contact a helpline in your region.")

    speak_and_print("The Thea development team emphasizes that while Thea aims to be supportive, it is not a licensed therapist. The AI is continually learning and evolving, and your feedback is valuable for its improvement. The Thea team does not take responsibility for any harm caused by the program; use it at your own risk.")

    disclaimer = "If you understand that Thea is not a real therapist and you have read and understood the disclaimer, please type 'y' to confirm: "

    
    speak_and_print(disclaimer)
    user_agree = input("type hear: ").lower()
    
    if user_agree == "y":
        break  # Break out of the loop if the user agrees to the terms of service
    elif user_agree == "admin code 110308":
        break

# Proceed with the therapy session
speak_and_print("Now, please state your name for easy communication")
name = input("Your Name: ")

#the session has started after the introduction
speak_and_print(f"I am Thea, your therapist for today, {name} remember that you can end the session whenever you what by saying `ok thank you for the session` to . Let's start. How are you feeling today?")

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
            
        elif user_statement == "ok thanks for the session":
            speak_and_print("Ok then see you next time")
            break
            
        if all(word not in user_statement for word in happy_list + sad_list + angry_list + depressed_list + suicidal_list):
            general_responses()
