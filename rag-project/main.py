import streamlit as st
from pathlib import Path
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
from streamlit_cookies_manager import EncryptedCookieManager
import streamlit.components.v1 as components
st.set_page_config(
    page_title="PDF Chat Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

embedding_model = OpenAIEmbeddings()

QDRANT_URL = st.secrets["QDRANT_URL"]
QDRANT_API_KEY = st.secrets["QDRANT_API_KEY"]

if not QDRANT_URL or not QDRANT_API_KEY:
    st.error("❌ Missing Qdrant configuration. Please set QDRANT_URL and QDRANT_API_KEY in your .env file")
    st.stop()

cookies = EncryptedCookieManager(
    prefix="pdf_chat_",
    password="your-secret-key-here-change-this-in-production"
)

def clear_all_browser_cookies():
    cookie_clear_js = """
    <script>
    function clearAllCookies() {
        // Clear all cookies for current domain
        const cookies = document.cookie.split(";");
        
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i];
            const eqPos = cookie.indexOf("=");
            const name = eqPos > -1 ? cookie.substr(0, eqPos).trim() : cookie.trim();
            
            // Clear for current path and domain
            document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;";
            document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=" + window.location.hostname + ";";
            document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=." + window.location.hostname + ";";
        }
        
        // Also clear localStorage and sessionStorage
        if (typeof(Storage) !== "undefined") {
            localStorage.clear();
            sessionStorage.clear();
        }
        
        console.log("All cookies and storage cleared!");
        
        // Signal completion to Streamlit
        window.parent.postMessage({type: 'cookies_cleared'}, '*');
    }
    
    // Execute immediately
    clearAllCookies();
    </script>
    """
    
    return components.html(cookie_clear_js, height=0)

def initialize_session_state():
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
        # REMOVED: "vector_store_cache": {}  # This was causing the pickle error
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

def check_cookie_authentication():
    if cookies.ready() and not st.session_state.authenticated:
        try:
            if cookies.get("authenticated") == "true" and cookies.get("username"):
                st.session_state.authenticated = True
                st.session_state.username = cookies.get("username")
                return True
        except Exception as e:
            st.write(f"Cookie read error: {e}")
    return False

if not st.session_state.authenticated:
    check_cookie_authentication()

def create_collection_name(filename: str) -> str:
    base_name = Path(filename).stem
    safe_name = "".join(c if c.isalnum() else "_" for c in base_name)
    if not safe_name[0].isalpha():
        safe_name = "pdf_" + safe_name
    return safe_name.lower()

def get_vector_store(collection_name: str):
    try:
        vector_store = QdrantVectorStore.from_existing_collection(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            collection_name=collection_name,
            embedding=embedding_model
        )
        return vector_store
    except Exception as e:
        vector_store = QdrantVectorStore.from_documents(
            documents=[],
            embedding=embedding_model,
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            collection_name=collection_name,
            force_recreate=True
        )
        return vector_store

def count_tokens(text: str, model: str = "gpt-4") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except:
        return len(text.split())

def verify_user(username, password):
    is_valid = username == "admin" and password == "admin123"
    
    if is_valid:
        try:
            if cookies.ready():
                cookies["authenticated"] = "true"
                cookies["username"] = username
                cookies.save()
        except Exception as e:
            st.write(f"Cookie save error: {e}")
    
    return is_valid

def perform_logout():
    clear_all_browser_cookies()
    
    try:
        if cookies.ready():
            cookies["authenticated"] = "false"
            cookies["username"] = ""
            cookies.save()
    except Exception as e:
        st.write(f"Cookie clear error: {e}")
    
    session_keys_to_keep = []
    for key in list(st.session_state.keys()):
        if key not in session_keys_to_keep:
            del st.session_state[key]
    
    initialize_session_state()
    
    time.sleep(0.1)

def show_auth_ui():
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
                st.info("💡 **Demo Credentials:** Username: admin, Password: admin123")
            
            st.markdown("</div>", unsafe_allow_html=True)

def main_app():
    with st.sidebar:
        st.markdown(f"### 👤 Welcome, **{st.session_state.username}**!")
        st.markdown("---")
        
        if not st.session_state.show_logout_confirmation:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.show_logout_confirmation = True
                st.rerun()
        else:
            st.warning("⚠️ Are you sure you want to logout?")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Yes", use_container_width=True):
                    st.session_state.just_logged_out = True
                    perform_logout()
                    st.rerun()
            
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.show_logout_confirmation = False
                    st.rerun()
        
        st.markdown("---")
        st.markdown("### 📄 Upload Document")
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type="pdf",
            key="pdf_uploader",
            help="Upload a PDF document to start chatting with it"
        )
        
        if uploaded_file is not None:
            if (st.session_state.current_file != uploaded_file.name or 
                not st.session_state.pdf_processed):
                
                st.session_state.processing = True
                st.session_state.pdf_processed = False
                st.session_state.current_file = uploaded_file.name
                
                collection_name = create_collection_name(uploaded_file.name)
                st.session_state.collection_name = collection_name
                
                with st.spinner("📄 Processing PDF..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        pdf_path = tmp_file.name
                    
                    try:
                        loader = PyPDFLoader(pdf_path)
                        documents = loader.load()
                        
                        text_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=1000,
                            chunk_overlap=200
                        )
                        chunks = text_splitter.split_documents(documents)
                        
                        vector_db = get_vector_store(collection_name)
                        vector_db.add_documents(chunks)
                        
                        st.session_state.pdf_processed = True
                        st.session_state.processing = False
                        st.success(f"✅ '{uploaded_file.name}' processed successfully!")
                        
                    except Exception as e:
                        st.error(f"❌ Error processing PDF: {str(e)}")
                        st.session_state.processing = False
                    finally:
                        try:
                            os.unlink(pdf_path)
                        except:
                            pass
        
        if st.session_state.current_file:
            st.markdown("---")
            st.markdown("### 📊 Current Document")
            st.info(f"📄 **File:** {st.session_state.current_file}")
            if st.session_state.pdf_processed:
                st.success("✅ **Status:** Processed & Ready")
            else:
                st.warning("⏳ **Status:** Processing...")

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

    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "timestamp" in message:
                    st.caption(f"🕒 {message['timestamp']}")

    if prompt := st.chat_input("💭 Ask a question about your PDF document..."):
        if not st.session_state.pdf_processed:
            st.warning("⚠️ Please upload and process a PDF document first!")
            st.stop()
        
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
    
    if (st.session_state.messages and 
        st.session_state.messages[-1]["role"] == "user" and 
        st.session_state.pdf_processed and 
        st.session_state.collection_name):
        
        last_user_message = st.session_state.messages[-1]["content"]
        
        if not last_user_message or last_user_message.strip() == "":
            st.error("⚠️ Empty message detected. Please enter a valid question.")
            st.session_state.messages.pop()
            st.rerun()
        
        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching for relevant information..."):
                try:
                    vector_db = get_vector_store(st.session_state.collection_name)
                    
                    search_results = vector_db.similarity_search(query=last_user_message, k=3)
                    
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

                    if not system_prompt or not last_user_message:
                        raise ValueError("Missing required content for API call")
                        
                    chat_completion = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": last_user_message},
                        ]
                    )
                    response = chat_completion.choices[0].message.content
                    
                except Exception as e:
                    st.error(f"❌ Error processing your request: {str(e)}")
                    response = "I'm sorry, I encountered an error while processing your request. Please try again."
                
                st.markdown(response)
                
                if "time_obj" in st.session_state.messages[-1]:
                    user_time = st.session_state.messages[-1]["time_obj"]
                    response_time = max(datetime.now(), user_time + timedelta(seconds=1))
                else:
                    response_time = datetime.now()
                    
                response_timestamp = response_time.strftime("%H:%M:%S")
                st.caption(f"🕒 {response_timestamp}")
                
                assistant_tokens = count_tokens(response)
                st.session_state.total_tokens += assistant_tokens
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": response_timestamp,
                    "tokens": assistant_tokens,
                    "time_obj": response_time  
                })
                
    if st.session_state.messages:
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.total_tokens = 0
                st.session_state.last_reset = datetime.now()
                st.rerun()

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📅 Session Started", st.session_state.last_reset.strftime('%H:%M:%S'))
    
    with col2:
        st.metric("🔢 Total Tokens", st.session_state.total_tokens)
    
    with col3:
        st.metric("💬 Messages", len(st.session_state.messages))


def main():
    if st.session_state.get("just_logged_out"):
        st.success("✅ Successfully logged out!")
        time.sleep(2)
        if "just_logged_out" in st.session_state:
            del st.session_state["just_logged_out"]

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

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"App crashed: {e}")