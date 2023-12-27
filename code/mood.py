import random
import pyttsx3

engine = pyttsx3.init("sapi5")
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)

def speak(audio):
    engine.say(audio)
    engine.runAndWait()
    
#list of word that trigger the responses 
happy_list = ["happy", "great", "good", "better", "joyful", "content", "fulfilled", "positive", "optimistic", "upbeat", "elated", "radiant", "grateful", "blissful", "satisfied", "cheerful", "exuberant", "vibrant", "ecstatic", "peaceful", "serene", "blessed", "delighted", "glorious", "heartened", "inspired", "triumphant", "zealous", "merry", "euphoric", "jovial", "gleeful", "festive", "lively", "spirited", "buoyant", "uplifting", "hopeful", "comforted", "empowered", "wonderful"]

sad_list = ["sad", "negative", "boring", "melancholy", "unhappy", "disheartened", "discouraged", "gloomy", "dismal", "despondent", "downcast", "mournful", "blue", "downhearted", "crestfallen", "dejected", "forlorn", "sullen", "somber", "lugubrious", "woeful", "heartbroken", "bereaved", "mournful", "pensive", "doleful", "woebegone", "disconsolate", "lugubrious", "wistful", "regretful", "downtrodden", "defeated", "low-spirited", "demoralized", "dispirited", "apathetic", "listless", "weary", "dreary", "stifled", "glum", "uninspired", "unmotivated", "unfulfilled"]

angry_list = ["angry", "irate", "enraged", "furious", "livid", "incensed", "outraged", "resentful", "indignant", "annoyed", "irritated", "agitated", "frustrated", "exasperated", "infuriated", "provoked", "cross", "mad", "upset", "offended", "vexed", "displeased", "hostile", "bitter", "resentful", "miffed", "peeved", "sulky", "testy", "tense", "grumpy", "irascible", "cranky", "impatient", "irate", "aggravated", "disgruntled", "exasperated", "hot-tempered", "short-tempered", "snappish", "touchy"]

depressed_list = ["depressed", "downhearted", "melancholic", "disheartened", "blue", "low", "despondent", "despairing", "dismal", "gloomy", "forlorn", "sorrowful", "mournful", "wretched", "hopeless", "discouraged", "downtrodden", "disconsolate", "downcast", "miserable", "heavy-hearted", "sad", "unhappy", "glum", "joyless", "lugubrious", "morose", "somber", "sullen", "woeful", "tearful", "weepy", "weeping", "sulky", "pessimistic", "defeated", "crestfallen", "brokenhearted", "dejected", "desolate", "heartbroken", "inconsolable", "morbid", "unconsolable"]

suicidal_list = ["suicidal", "hopeless", "desperate", "worthless", "overwhelmed", "lost", "trapped", "unbearable", "broken", "alone", "helpless", "painful", "endless", "darkness", "ending it", "ending my life", "cannot go on", "no way out", "giving up", "life is meaningless", "thinking of suicide", "suicide thoughts", "ending it all", "just want it to stop", "can't go on", "want to die", "don't want to live", "no reason to live", "wish I were dead", "I'm a burden", "tired of life", "nothing to live for", "fade away", "wish it would end", "permanent solution", "escape the pain", "end the suffering", "last resort"]

# def for mood specificy responses 
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
    
def suicidal_mood_responses():
        responses = [
        "I'm really sorry to hear that you're feeling this way. It's important to talk to someone who can provide support.",
        "It's okay to ask for help. Consider reaching out to a friend, family member, or mental health professional.",
        "You're not alone. Many people care about you, and there are resources available to support you.",
        "Please don't hesitate to talk to someone you trust about your feelings. They may be able to offer assistance and comfort.",
        "I'm here for you, but it's crucial to connect with those who can provide immediate help. Consider contacting a helpline or a mental health professional.",
        "Remember, your feelings are valid, and seeking help is a sign of strength.",
        "Even in the darkest moments, there is hope. Reach out to someone you trust and let them support you.",
        "Taking the first step to talk about your feelings is a brave and important decision. You're not alone on this journey.",
        "Your well-being matters, and there are people who want to help. Consider speaking to a mental health professional for guidance.",
        "It's important to prioritize your safety. Connect with someone you trust or a mental health professional as soon as possible.",
        "If you're struggling, please don't face it alone. Reach out to someone who cares about you or contact a mental health helpline.",
        ]
        responses = random.choice(responses)
        print(f"Thea: {responses}")
        speak(responses) 
    
def general_responses():
    responses = [
        "Okay, can you tell me more?",
        "I'm here to listen. Please share more.",
        "I'm interested in hearing more. Go ahead.",
        "Feel free to elaborate. What else is on your mind?",
        "You have my attention. Share more details, if you'd like.",
        "I'm here to help. Tell me more about it.",
        "I appreciate your openness. Is there anything specific you'd like to discuss?",
        "Your thoughts are important. Let's explore them together.",
        "Thank you for sharing. Is there a particular aspect you want to focus on?",
        "I'm here to support you. What would you like to talk about?",
        "In our conversation, your comfort is a priority. Feel free to express yourself.",
        "Your feelings matter. How can I assist you today?",
        "Sharing your thoughts is a positive step. What else would you like to share?",
        "It's okay to take your time. When you're ready, I'm here to listen.",
        "Your perspective is valuable. Can you provide more details?",
        "I'm curious to learn more about your thoughts. Please share when you're ready.",
        "Every conversation is a chance for understanding. What would you like to discuss?",
        "Your emotions are valid. Let's navigate through them together.",
        "Thank you for opening up. How can we make this conversation most helpful for you?",
    ]

    response = random.choice(responses)
    print(f"Thea: {response}")
    speak(response)
