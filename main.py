import datetime
import random
import speech_recognition as sr
import pyttsx3

engine = pyttsx3.init("sapi5")
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)

#list of words
happy_list = ["happy", "great", "good", "better", "joyful", "content", "fulfilled", "positive", "optimistic", "upbeat", "elated", "radiant", "grateful", "blissful", "satisfied", "cheerful", "exuberant", "vibrant", "ecstatic", "peaceful", "serene", "blessed", "delighted", "glorious", "heartened", "inspired", "triumphant", "zealous", "merry", "euphoric", "jovial", "gleeful", "festive", "lively", "spirited", "buoyant", "uplifting", "hopeful", "comforted", "empowered"]

sad_list = ["sad", "negative", "boring", "melancholy", "unhappy", "disheartened", "discouraged", "gloomy", "dismal", "despondent", "downcast", "mournful", "blue", "downhearted", "crestfallen", "dejected", "forlorn", "sullen", "somber", "lugubrious", "woeful", "heartbroken", "bereaved", "mournful", "pensive", "doleful", "woebegone", "disconsolate", "lugubrious", "wistful", "regretful", "downtrodden", "defeated", "low-spirited", "demoralized", "dispirited", "apathetic", "listless", "weary", "dreary", "stifled", "glum", "uninspired", "unmotivated", "unfulfilled"]

angry_list = ["angry", "irate", "enraged", "furious", "livid", "incensed", "outraged", "resentful", "indignant", "annoyed", "irritated", "agitated", "frustrated", "exasperated", "infuriated", "provoked", "cross", "mad", "upset", "offended", "vexed", "displeased", "hostile", "bitter", "resentful", "miffed", "peeved", "sulky", "testy", "tense", "grumpy", "irascible", "cranky", "impatient", "irate", "aggravated", "disgruntled", "exasperated", "hot-tempered", "short-tempered", "snappish", "touchy"]

depressed_list = ["depressed", "downhearted", "melancholic", "disheartened", "blue", "low", "despondent", "despairing", "dismal", "gloomy", "forlorn", "sorrowful", "mournful", "wretched", "hopeless", "discouraged", "downtrodden", "disconsolate", "downcast", "miserable", "heavy-hearted", "sad", "unhappy", "glum", "joyless", "lugubrious", "morose", "somber", "sullen", "woeful", "tearful", "weepy", "weeping", "sulky", "pessimistic", "defeated", "crestfallen", "brokenhearted", "dejected", "desolate", "heartbroken", "inconsolable", "morbid", "unconsolable"]


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

wishme()

def speak_and_print(message):
    print(message)
    speak(message)

speak_and_print("Before we start today, please state your name for easy communication")
name = input("Your Name: ")
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
        "I knew you could do it!",
        "Your success is well-deserved.",
        "I'm impressed by your achievements.",
        "You're on fire today!",
        "Congratulations! This is wonderful!",
        "You're a star!",
        "Your positivity is contagious.",
        "I can see the joy in your words.",
        "You must be so proud!",
        "What an accomplishment!",
        "Your hard work is paying off.",
        "This is a major win!",
        "You're unstoppable!",
        "I'm thrilled to hear about your success.",
        "Keep shining bright!",
        "You've got the Midas touch!",
        "I'm smiling just hearing about it!",
        "This is a cause for celebration!",
        "The world is better with your positivity in it."
    ]
    response = random.choice(responses)
    print(f"Thea: {response}")
    speak(response)

def sad_mood_responses():
    responses = [
        "I understand it's a tough time for you.",
        "You're not alone; I'm here to support you.",
        "It's okay to feel a bit down sometimes.",
        "I'm here to listen and help you navigate through your emotions.",
        "Take a deep breath; we can work through this together.",
        "Remember, emotions are a natural part of being human.",
        "Feel free to share more about what's on your mind; I'm here to listen.",
        "In challenging times, expressing your feelings can be a positive step.",
        "Your emotions are valid; let's explore them together.",
        "You have the strength to overcome these feelings.",
        "I appreciate your openness in sharing your emotions.",
        "Let's find ways to bring a bit of light into your day.",
        "It's okay not to be okay; we'll take one step at a time.",
        "Your well-being is important, and I'm here to support you.",
        "Sometimes, acknowledging your emotions is the first step towards healing."
    ]
    response = random.choice(responses)
    print(f"Thea: {response}")
    speak(response)

def angry_mood_responses():
    responses = [
        "I can sense your frustration; it's okay to feel angry.",
        "Anger is a powerful emotion. Let's explore what triggered it.",
        "Your feelings are valid, including anger. What happened?",
        "Expressing anger is a natural part of being human. Let's discuss it.",
        "Anger can be a signal. What do you think might be the root cause?",
        "It's alright to be angry; let's find a constructive way to address it.",
        "I'm here to listen without judgment. What's on your mind?",
        "Anger can be a motivator for change. How can we channel it positively?",
        "Take a moment to breathe. We can work through the source of your anger.",
        "Remember, it's okay to set boundaries and express your needs.",
        "Let's find a solution together. Your perspective is important.",
        "Anger is a temporary emotion; we'll find a way to navigate through it.",
        "In moments of anger, self-reflection can lead to growth. What are you feeling?",
        "I appreciate your honesty about your emotions. Let's address them together."
    ]
    response = random.choice(responses)
    print(f"Thea: {response}")
    speak(response)


def depressed_mood_responses():
    responses = [
        "I'm truly sorry to hear that you're feeling this way.",
        "You're not alone; I'm here to support you through this.",
        "It's okay to feel overwhelmed. We'll take things step by step.",
        "You have the strength to navigate through these emotions.",
        "You don't have to face it alone; I'm here to listen and help.",
        "Let's explore these feelings together in a safe and supportive space.",
        "Your well-being is important, and I'm here to offer assistance.",
        "Reaching out for help is a brave step. I'm here for you.",
        "In difficult times, small steps can lead to positive changes.",
        "You're not alone in facing challenges. Many have found their way to healing.",
        "It's okay to seek support; we can work through this together.",
        "Your feelings are valid, and I'm here to provide a listening ear.",
        "We'll find coping strategies together to make things more manageable.",
        "Taking care of your mental health is a courageous choice. Let's do it together."
    ]
    response = random.choice(responses)
    print(f"Thea: {response}")
    speak(response)



if __name__ == "__main__":
    
    while True:
        user_statement = takecommand().lower()

        if any(word in user_statement for word in happy_list):
            happy_mood_responses()

        if any(word in user_statement for word in sad_list):
            sad_mood_responses()

        elif any(word in user_statement for word in angry_list):
            angry_mood_responses()

        elif any(word in user_statement for word in depressed_list):
            depressed_mood_responses()

        else:
            print("I can't answer you. I'm sorry.")
            speak("I can't answer you. I'm sorry.")
