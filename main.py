import pandas as pd

# Load the dataset
df = pd.read_csv("therapy_chatbot_nlp_dataset.csv")

# Check if the column exists
if "user_input" not in df.columns:
    # Create the column
    df["user_input"] = df["user_input"].str.lower()

# Preprocess the data
# ...
