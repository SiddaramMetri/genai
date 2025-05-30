from dotenv import load_dotenv

from openai import OpenAI

load_dotenv()

client = OpenAI()

text = "Dog chases cat"

response = client.embeddings.create(
    model="text-embedding-3-small",
    input=text
)

print("Vector Embedding:", response.data[0].embedding)
print("Vector length:", len(response.data[0].embedding))