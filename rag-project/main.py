import streamlit as st
import logging
from pathlib import Path
from dotenv import load_dotenv
import os
import time
from datetime import datetime, timedelta
import tempfile
import tiktoken
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="PDF Chat Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Try to import optional dependencies
try:
    from streamlit_cookies_manager import EncryptedCookieManager
    COOKIES_AVAILABLE = True
except ImportError:
    COOKIES_AVAILABLE = False
    logger.warning("Cookie manager not available - authentication will not persist")

def get_environment_variables():
    """Get and validate environment variables"""
    env_vars = {
        'QDRANT_URL': os.getenv("QDRANT_URL"),
        'QDRANT_API_KEY': os.getenv("QDRANT_API_KEY"),
        'OPENAI_API_KEY': os.getenv("OPENAI_API_KEY"),
        'COOKIE_SECRET': os.getenv("COOKIE_SECRET", "default-dev-password-change-in-prod"),
        'APP_USERNAME': os.getenv("APP_USERNAME", "admin"),
        'APP_PASSWORD': os.getenv("APP_PASSWORD", "admin123")
    }
    
    # Check critical environment variables
    missing_vars = []
    for var in ['QDRANT_URL', 'QDRANT_API_KEY', 'OPENAI_API_KEY']:
        if not env_vars[var]:
            missing_vars.append(var)
    
    if missing_vars:
        st.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        st.info("""
        **For Streamlit Cloud:**
        1. Go to your app settings
        2. Add these variables in the 'Secrets' section
        
        **For local development:**
        Create a .env file with:
        ```
        QDRANT_URL=your_qdrant_url
        QDRANT_API_KEY=your_qdrant_api_key
        OPENAI_API_KEY=your_openai_api_key
        COOKIE_SECRET=your_secure_random_string
        APP_USERNAME=your_username
        APP_PASSWORD=your_password
        ```
        """)
        st.stop()
    
    return env_vars

# Get environment variables
try:
    env_vars = get_environment_variables()
except Exception as e:
    st.error(f"Configuration error: {str(e)}")
    st.stop()

# Initialize OpenAI client
try:
    client = OpenAI(api_key=env_vars['OPENAI_API_KEY'])
    embedding_model = OpenAIEmbeddings(openai_api_key=env_vars['OPENAI_API_KEY'])
except Exception as e:
    st.error(f"❌ Failed to initialize OpenAI client: {str(e)}")
    st.stop()

# Initialize cookie manager if available
cookies = None
if COOKIES_AVAILABLE:
    try:
        cookies = EncryptedCookieManager(
            prefix="pdf_chat_",
            password=env_vars['COOKIE_SECRET']
        )
    except Exception as e:
        logger.warning(f"Failed to initialize cookie manager: {str(e)}")
        COOKIES_AVAILABLE = False

def initialize_session_state():
    """Initialize session state with default values"""
    defaults = {
        "authenticated": False,
        "username": None,
        "total_tokens": 0,
        "chat_history": [],
        "last_reset": datetime.now(),
        "messages": [],
        "pdf_processed": False,
        "processing": False,
        "current_file": None,
        "show_clear_confirmation": False,
        "show_logout_confirmation": False,
        "collection_name": None,
        "logout_clicked": False,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def check_cookie_authentication():
    """Check if user is authenticated via cookies"""
    if not COOKIES_AVAILABLE or not cookies:
        return False
        
    if cookies.ready() and not st.session_state.authenticated:
        try:
            if cookies.get("authenticated") == "true" and cookies.get("username"):
                st.session_state.authenticated = True
                st.session_state.username = cookies.get("username")
                return True
        except Exception as e:
            logger.warning(f"Cookie read error: {e}")
    return False

def create_collection_name(filename: str) -> str:
    """Create a safe collection name from filename"""
    base_name = Path(filename).stem
    safe_name = "".join(c if c.isalnum() else "_" for c in base_name)
    if not safe_name or not safe_name[0].isalpha():
        safe_name = "pdf_" + safe_name
    return safe_name.lower()[:50]  # Limit length

def get_vector_store(collection_name: str):
    """Get or create vector store"""
    try:
        vector_store = QdrantVectorStore.from_existing_collection(
            url=env_vars['QDRANT_URL'],
            api_key=env_vars['QDRANT_API_KEY'],
            collection_name=collection_name,
            embedding=embedding_model
        )
        return vector_store
    except Exception as e:
        logger.info(f"Creating new collection: {collection_name}")
        vector_store = QdrantVectorStore.from_documents(
            documents=[],
            embedding=embedding_model,
            url=env_vars['QDRANT_URL'],
            api_key=env_vars['QDRANT_API_KEY'],
            collection_name=collection_name,
            force_recreate=True
        )
        return vector_store

def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """Count tokens in text"""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback to word count estimation
        return len(text.split()) * 1.3

def verify_user(username: str, password: str) -> bool:
    """Verify user credentials"""
    is_valid = (username == env_vars['APP_USERNAME'] and 
                password == env_vars['APP_PASSWORD'])
    
    if is_valid and COOKIES_AVAILABLE and cookies:
        try:
            if cookies.ready():
                cookies["authenticated"] = "true"
                cookies["username"] = username
                cookies.save()
        except Exception as e:
            logger.warning(f"Cookie save error: {e}")
    
    return is_valid

def perform_logout():
    """Perform user logout"""
    # Clear cookies if available
    if COOKIES_AVAILABLE and cookies:
        try:
            if cookies.ready():
                cookies["authenticated"] = "false"
                cookies["username"] = ""
                cookies.save()
        except Exception as e:
            logger.warning(f"Cookie clear error: {e}")
    
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    initialize_session_state()
    st.session_state.just_logged_out = True

def show_auth_ui():
    """Display authentication UI"""
    if st.session_state.get("just_logged_out"):
        st.success("✅ Successfully logged out!")
        del st.session_state["just_logged_out"]
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            with st.form("login_form", clear_on_submit=True):
                st.subheader("🔐 Login")
                st.markdown("---")
                
                username = st.text_input("👤 Username", placeholder="Enter your username")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    submit = st.form_submit_button("🚀 Login", use_container_width=True)
                
                if submit:
                    if not username or not password:
                        st.error("❌ Please enter both username and password")
                    elif verify_user(username, password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.success("✅ Login successful! Redirecting...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                
                st.markdown("---")
                if env_vars['APP_USERNAME'] == 'admin' and env_vars['APP_PASSWORD'] == 'admin123':
                    st.info("💡 **Demo Credentials:** Username: admin, Password: admin123")

def process_pdf(uploaded_file):
    """Process uploaded PDF file"""
    try:
        collection_name = create_collection_name(uploaded_file.name)
        st.session_state.collection_name = collection_name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            pdf_path = tmp_file.name
        
        # Load and split PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)
        
        # Add to vector store
        vector_db = get_vector_store(collection_name)
        vector_db.add_documents(chunks)
        
        st.session_state.pdf_processed = True
        st.session_state.processing = False
        st.success(f"✅ '{uploaded_file.name}' processed successfully!")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error processing PDF: {str(e)}")
        st.session_state.processing = False
        return False
    finally:
        try:
            os.unlink(pdf_path)
        except:
            pass

def get_ai_response(question: str, collection_name: str) -> str:
    """Get AI response for the question"""
    try:
        vector_db = get_vector_store(collection_name)
        search_results = vector_db.similarity_search(query=question, k=3)
        
        context = "\n\n\n".join([
            f"Page Content: {result.page_content}\nPage Number: {result.metadata.get('page_label', 'N/A')}\nFile Location: {result.metadata.get('source', 'N/A')}" 
            for result in search_results
        ])

        system_prompt = f"""
        You are a PDF content AI assistant. Your job is to answer questions ONLY using information from the provided PDF context.

        RULES:
        - If the answer is in the PDF context below → Answer with page citation
        - If the answer is NOT in the PDF context below → Say: "I'm sorry, I don't have information about that in this PDF. Please ask about something else from the document."
        - Never use outside knowledge
        - Never guess or infer beyond what's written
        - Always cite the page number when possible

        PDF Context:
        {context}
        """

        chat_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            max_tokens=1000,
            temperature=0.1
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error getting AI response: {str(e)}")
        return "I'm sorry, I encountered an error while processing your request. Please try again."

def main_app():
    """Main application interface"""
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 Welcome, **{st.session_state.username}**!")
        st.markdown("---")
        
        # Logout button
        if not st.session_state.show_logout_confirmation:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.show_logout_confirmation = True
                st.rerun()
        else:
            st.warning("⚠️ Are you sure you want to logout?")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Yes", use_container_width=True):
                    perform_logout()
                    st.rerun()
            
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.show_logout_confirmation = False
                    st.rerun()
        
        st.markdown("---")
        st.markdown("### 📄 Upload Document")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type="pdf",
            key="pdf_uploader",
            help="Upload a PDF document to start chatting with it"
        )
        
        # Process uploaded file
        if uploaded_file is not None:
            if (st.session_state.current_file != uploaded_file.name or 
                not st.session_state.pdf_processed):
                
                st.session_state.processing = True
                st.session_state.pdf_processed = False
                st.session_state.current_file = uploaded_file.name
                
                with st.spinner("📄 Processing PDF..."):
                    process_pdf(uploaded_file)
        
        # Current document status
        if st.session_state.current_file:
            st.markdown("---")
            st.markdown("### 📊 Current Document")
            st.info(f"📄 **File:** {st.session_state.current_file}")
            if st.session_state.pdf_processed:
                st.success("✅ **Status:** Processed & Ready")
            else:
                st.warning("⏳ **Status:** Processing...")

    # Main content
    st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h1 style='font-size: 2.5rem; font-weight: 700; margin-bottom: 1rem;'>
                💬 Chat with your PDF
            </h1>
            <p style='color: #64748b; font-size: 1.1rem;'>
                Upload your PDF document and start asking questions
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Chat interface
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "timestamp" in message:
                    st.caption(f"🕒 {message['timestamp']}")

    # Chat input
    if prompt := st.chat_input("💭 Ask a question about your PDF document..."):
        if not st.session_state.pdf_processed:
            st.warning("⚠️ Please upload and process a PDF document first!")
            st.stop()
        
        # Add user message
        current_time = datetime.now()
        timestamp = current_time.strftime("%H:%M:%S")
        user_tokens = count_tokens(prompt)
        
        st.session_state.total_tokens += user_tokens
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": timestamp,
            "tokens": user_tokens,
            "time_obj": current_time
        })
        
        st.rerun()
    
    # Generate AI response
    if (st.session_state.messages and 
        st.session_state.messages[-1]["role"] == "user" and 
        st.session_state.pdf_processed and 
        st.session_state.collection_name):
        
        last_user_message = st.session_state.messages[-1]["content"]
        
        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching for relevant information..."):
                response = get_ai_response(last_user_message, st.session_state.collection_name)
                
                st.markdown(response)
                
                # Add timestamp
                if "time_obj" in st.session_state.messages[-1]:
                    user_time = st.session_state.messages[-1]["time_obj"]
                    response_time = max(datetime.now(), user_time + timedelta(seconds=1))
                else:
                    response_time = datetime.now()
                    
                response_timestamp = response_time.strftime("%H:%M:%S")
                st.caption(f"🕒 {response_timestamp}")
                
                # Track tokens
                assistant_tokens = count_tokens(response)
                st.session_state.total_tokens += assistant_tokens
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": response_timestamp,
                    "tokens": assistant_tokens,
                    "time_obj": response_time  
                })
    
    # Clear chat button
    if st.session_state.messages:
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.total_tokens = 0
                st.session_state.last_reset = datetime.now()
                st.rerun()

    # Statistics
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📅 Session Started", st.session_state.last_reset.strftime('%H:%M:%S'))
    
    with col2:
        st.metric("🔢 Total Tokens", st.session_state.total_tokens)
    
    with col3:
        st.metric("💬 Messages", len(st.session_state.messages))

def main():
    """Main application entry point"""
    try:
        initialize_session_state()
        
        # Check cookie authentication
        if not st.session_state.authenticated:
            check_cookie_authentication()
        
        # Show appropriate interface
        if not st.session_state.authenticated:
            st.markdown("""
                <div style='text-align: center; margin-bottom: 3rem;'>
                    <h1 style='font-size: 3rem; font-weight: 700; margin-bottom: 1rem;'>
                        📚 PDF Chat Assistant
                    </h1>
                    <p style='color: #64748b; font-size: 1.2rem;'>
                        Secure login required to access the application
                    </p>
                </div>
            """, unsafe_allow_html=True)
            show_auth_ui()
        else:
            main_app()
            
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please refresh the page or contact support if the issue persists.")
        logger.error(f"Application error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()