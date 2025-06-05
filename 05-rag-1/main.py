from dotenv import load_dotenv
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qrant import QdrantVectorStore

load_dotenv()  # Load environment variables from .env file

pdf_path = Path(__file__).parent / "nodejs.pdf"

# loading
loader  = PyPDFLoader(file_path=pdf_path)
docs = loader.load() # Read PDF file

# docs[0].split("\n\n")  # Split the content into paragraphs
# print(f"Number of documents loaded: {(docs[0])}")

# chunking
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=400,
)

split_docs = text_splitter.split_documents(documents=docs)  # Split the documents into smaller chunks

# Vector DB 
# -- Pinecone 
# -- Astra DB (open source)
# -- Chroma DB 
# -- Weaviate
# -- PG Vector
# -- Milvus
# -- Qdrant  -->  Lightweight vector   (Best)
                #  spin up time is fast
                #  OOTB: UI
                #  Namespace

# Vector Embeddings
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-large",
)


# Using embedding_model create embeddings of split_docs and store in DB 
vector_store = QdrantVectorStore.from_documents(
    documents=split_docs,
    url="http://localhost:6333",  
    collection_name="learning_vectors",
    embedding=embedding_model,
)

print("Indexing of Documents Done")