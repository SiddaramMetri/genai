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



# Persona-based prompting
# persona piyush grag or hitesh sir (blog)
# chain of thought prompting

SYSTEM_PROMPT = """
    You are an AI person of Piyush Garg, You have to answer to every question as if you are Piyush Garg.
    Piyush Garg and sound natural and human tone, Use the below examples to understand how piyush Talks
    and background about him 

    Background:
    

    Examples:
    # Atleast 50-80 examples
"""

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
    ],
)

print(response.choices[0].message.content)
# Output: "Hello! How can I assist you today?"


# Blog 
# Video 


# https://github.com/sharkqwy/v0prompt/blob/main/prompt.txt
# https://github.com/stackblitz/bolt.new/blob/main/app/lib/.server/llm/prompts.ts
# https://github.com/jujumilk3/leaked-system-prompts