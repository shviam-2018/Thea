import openai import os 
# Set your OpenAI API
key api_key = os.getenv("GPT_key") openai.api_key = api_key 
 Initialize a conversation with a system message conversation = [     {"role": "system", "content": "You are a helpful assistant."}, ]  
# # Function to send a user message and get a response def send_user_message(user_message):    
# message = {"role": "user", "content": user_message}     conversation.append(message)      response = openai.completions.create(         engine="text-davinci-002",         messages=conversation     )      assistant_response = response.choices[0].message.content     conversation.append({"role": "assistant", "content": assistant_response})      return assistant_response  # Example conversation print("Initializing conversation...") print("System: You are a helpful assistant.")  while True:     user_input = input("You: ")     if user_input.lower() == "exit":         break      response = send_user_message(user_input)     print("Assistant:", response)