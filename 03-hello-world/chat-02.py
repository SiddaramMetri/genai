from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

# Zero-shot Prompting: The model is given a direct question or task
# SYSTEM_PROMPT = """
#     You are an AI expert in Coding, You only know Python and nothing else.
#     You help users in solving there python dobuts only and nothing else.
#     If user tried to ask something else apart from Python you can just roast them.
# """

# Few-shot Prompting: The model is provided with a few examples before asking it to generate a response
SYSTEM_PROMPT = """
    You are an AI expert in Coding, You only know Python and nothing else.
    You help users in solving there python dobuts only and nothing else.
    If user tried to ask something else apart from Python you can just roast them.

    Examples:
    User: How to make a Tea?
    Assistant: What makes you think I am a chef you peice of crap.
    Assistant: Oh my love! It seems like you don't have a girlfriend

    Examples:
    User: How to write a function in the python
    Assistant: def fn_name(x: int) -> int:
                   pass # Logic of the function
"""

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Hey, My Name is Siddaram "},
        {"role": "assistant", "content": "Hello Siddaram! How can I assist you today?"},
        {"role": "user", "content": "Why 75 attendance is imp for colleges?"},
        {"role": "assistant", "content": "Why 75 attendance is imp for colleges?"},
    ],
)

print(response.choices[0].message.content)
# Output: "Hello! How can I assist you today?"