import tiktoken

enc = tiktoken.encoding_for_model("gpt-4o")

text = "Hello, world! This is a test of the tiktoken library."
tokens = enc.encode(text)
print(f"Text: {tokens}")

# Text: [13225, 11, 2375, 0, 1328, 382, 261, 1746, 328, 290, 260, 8251, 2488, 11282, 13]