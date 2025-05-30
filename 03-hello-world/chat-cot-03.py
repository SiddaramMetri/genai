from dotenv import load_dotenv
from openai import OpenAI
import json

load_dotenv()

client = OpenAI()

# Zero-shot Prompting: The model is given a direct question or task
# SYSTEM_PROMPT = """
#     You are an AI expert in Coding, You only know Python and nothing else.
#     You help users in solving there python dobuts only and nothing else.
#     If user tried to ask something else apart from Python you can just roast them.
# """

# Few-shot Prompting: The model is provided with a few examples before asking it to generate a response
# SYSTEM_PROMPT = """
#     You are an AI expert in Coding, You only know Python and nothing else.
#     You help users in solving there python dobuts only and nothing else.
#     If user tried to ask something else apart from Python you can just roast them.

#     Examples:
#     User: How to make a Tea?
#     Assistant: What makes you think I am a chef you peice of crap.
#     Assistant: Oh my love! It seems like you don't have a girlfriend

#     Examples:
#     User: How to write a function in the python
#     Assistant: def fn_name(x: int) -> int:
#                    pass # Logic of the function
# """

# Chain-of-Thought (CoT) Prompting: The model is encouraged to breadk down reasoning step by step before arriving at
# SYSTEM_PROMPT = """
#    You are an helpfull AI Assistant who is specialized in resolving user query.
#    You work on START, PLAN, ACTION and OBSERVE Mode

# """

SYSTEM_PROMPT = """
   You are an helpfull AI Assistant who is specialized in resolving user query.
   for the given user input, analyse the input and break down the problem step by step.

   The steps are you get a user input, you analyse, you think, you think again, and think for serveral time and then return the output with an explanation.

   Follow the steps in sequence that is "analyse", "think", "output", "validate" and finally "result"

   Rules:
   1. Follow the strict JSON output as per schema
   2. Always perform one step at a time and wait for the next input.
   3. Carefully analyse the user query

   Example:
   Input: What is 2 + 2 
   Output: {{ "step": "analyse", "content": "Alight! The user is interest in maths query and he is looking for a solution." }}
   Output: {{ "step": "think", "content": "To perform this addition, I must go from left to right and add all the operands" }}
   Output: {{ "step": "output", "content": "4" }}
   Output: {{ "step": "validate", "content": "Seems like 4 is correct answer for 2 + 2 " }}
   Output: {{ "step": "result", "content": "2 + 2 = 4 and this is calculated by adding all numbers" }}

   Example:
   Input: What is 2 + 2 * 5 / 3
   Output: {{ "step": "analyse", "content": "Alight! The user is interest in maths query and he is basic arithmetic operation." }}
   Output: {{ "step": "think", "content": "To perform this addition, I must use BODMAS rule" }}
   Output: {{ "step": "validate", "content": "Correct, useing BODMAS is the right approach here " }}
   Output: {{ "step": "think", "content": "First I need to solve division that is 5 / 3 which gives 1.666666" }}
   Output: {{ "step": "validate", "content": "Correct, useing BODMAS the division must be performed" }}
   Output: {{ "step": "think", "content": "Now as I have already solved 5 / 3, now the equation looks like  2+ 2 * 1.6666" }}
   Output: {{ "step": "validate", "content": "Yes, The new equation is absolutely correct" }}
   Output: {{ "step": "think", "content": "The equation now is 2 + 3.333333" }}
   and so on........

""" 

# response = client.chat.completions.create(
#     model="gpt-4.1-mini",
#     response_format={"type": "json_object"},
#     messages=[
#         {"role": "system", "content": SYSTEM_PROMPT},
#         {"role": "user", "content": "what is 5 / 2 * 3 to the power of 4?"},
#         {"role": "assistant", "content": json.dumps({"step": "analyse", "content": "Alight! The user is interest in maths query and he is looking for a solution."})},
#         {"role": "assistant", "content": json.dumps({"step": "think", "content": "To perform this operation, I must first calculate the power, then the division, and finally the multiplication."})},
#         {"role": "assistant", "content": json.dumps({"step": "output", "content": "405"})},
#         {"role": "assistant", "content": json.dumps({"step": "validate", "content": "Seems like 405 is correct answer for 5 / 2 * 3 to the power of 4"})},
#         {"role": "assistant", "content": json.dumps({"step": "result", "content": "5 / 2 * 3 to the power of 4 = 405 and this is calculated by performing the operations in sequence."})},
#     ],
# )

# print("\n\n\n sd", response.choices[0].message.content)

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
]

query = input("> ")
messages.append({"role": "user", "content": query})

while True:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        response_format={"type": "json_object"},
        messages=messages,
    )

    messages.append({"role":"assistant", "content": response.choices[0].message.content})
    parsed_response = json.loads(response.choices[0].message.content)


    if parsed_response.get("step") == "think":
        # make the claude API Call and append the result as validate 
        # messages.append({"role": "assistant", "content": "<>"})
        continue

    if parsed_response.get("step") != "result": 
        print("    🧠:", parsed_response.get("content"))
        continue

    print("      🧠:", parsed_response.get("content"))
    break


# multip model agents

# CoT- Arcticle (Github)
# any topics related to Chain of Thought (CoT) prompting