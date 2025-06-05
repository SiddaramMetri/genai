# PDF Chat Assistant

A Streamlit-based application that allows you to upload PDF documents and chat with them using AI. The application uses Qdrant for vector storage and OpenAI's GPT-4 for generating responses.

## Prerequisites

- Python 3.8 or higher
- Qdrant server running locally (default: http://localhost:6333)
- OpenAI API key

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. The application uses remote .env files for configuration. Make sure you have access to the required environment variables:
   - OPENAI_API_KEY: Your OpenAI API key for embeddings and chat completions
   - Other environment variables as needed for your deployment

## Running the Application

1. Make sure your Qdrant server is running
2. Start the Streamlit app:
   ```bash
   streamlit run main.py
   ```
3. Open your browser and navigate to the URL shown in the terminal (usually http://localhost:8501)

## Features

- PDF document upload and processing
- Automatic text chunking and embedding
- Vector similarity search using Qdrant
- Interactive chat interface
- Page reference tracking
- Chat history persistence during session

## Usage

1. Upload a PDF document using the file uploader
2. Wait for the document to be processed and indexed
3. Start asking questions about the document in the chat interface
4. The AI will respond with relevant information and page references

## Note

Make sure you have enough disk space for the Qdrant database and that your OpenAI API key has sufficient credits for the embeddings and chat completions. 