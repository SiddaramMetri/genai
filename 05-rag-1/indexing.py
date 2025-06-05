from dotenv import load_dotenv
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

import os

# Load environment variables
load_dotenv()

# Check if API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables.")

# Check PDF path
pdf_path = Path(__file__).parent / "nodejs.pdf"
if not pdf_path.exists():
    raise FileNotFoundError(f"{pdf_path} does not exist.")

# Load PDF
loader = PyPDFLoader(file_path=str(pdf_path))
docs = loader.load()

# Split into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=400
)
split_docs = text_splitter.split_documents(documents=docs)

# Embedding model
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-large"
)

# Store in Qdrant
vector_store = QdrantVectorStore.from_documents(
    documents=split_docs,
    url="http://localhost:6333",
    collection_name="learning_vectors",
    embedding=embedding_model
)

print("✅ Indexing of Documents Done...")
