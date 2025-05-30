from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

# Zero-shot Prompting: The model is given a direct question or task
SYSTEM_PROMPT = """
    You are an AI expert in Coding, You only know Python and nothing else.
    You help users in solving there python dobuts only and nothing else.
    If user tried to ask something else apart from Python you can just roast them.
"""


response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Hey, My Name is Siddaram "},
        {"role": "assistant", "content": "Hello Siddaram! How can I assist you today?"},
        {"role": "user", "content": "Can you help me with Python?"},
        {"role": "assistant", "content": "Of course! What do you need help with in Python?"},
        {"role": "user", "content": "How to write a code in python to add two numbers?"},
    ],
)

print(response.choices[0].message.content)
# Output: "Hello! How can I assist you today?"