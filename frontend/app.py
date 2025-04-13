import streamlit as st
from streamlit_chat import message
from services.api_client import search_data
from renderer import render_result

st.set_page_config(page_title="FoodWise AI Assistant", layout="wide")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Title & Instructions ---
st.title("FoodWise Chatbot")
st.markdown("Ask me something and I’ll search for matching images from the knowledge base.")


# --- Side Bar Upload files ---
st.sidebar.header("Upload Files")
uploaded_files = st.sidebar.file_uploader(
    "Drag and drop files here", accept_multiple_files=True
)

# --- Content type selection ---
st.subheader("Select content type")
content_options = {
    "Q&A": "qa",
    "Blog": "blog",
    "PPT": "ppt",
    "PDF": "pdf",
    "Image": "image"
}

# Streamlit radio button UI
selected_type = st.radio(
    label="Choose content type:",
    options=list(content_options.keys()),
    horizontal=True,
    key="content_type_selection"
)

# --- Chat Input ---
user_input = st.chat_input("Type your query here...")

# --- Handle User Input ---
if user_input:
    if not selected_type:
        st.warning("⚠️ Please select a content type before submitting your query.")
    else:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.spinner("Searching for results..."):
            # Map selection to backend value
            selected_key = content_options[selected_type]

            # Map selected content type to collections
            collection_map = {
                "image": ["image"],
                "qa": ["blog", "ppt", "pdf"],
                "blog": ["blog", "ppt", "pdf"],
                "ppt": ["blog", "ppt", "pdf"],
                "pdf": ["blog", "ppt", "pdf"]
            }
            collections = collection_map.get(selected_key, ["blog", "ppt", "pdf"])

            result = search_data(
                query=user_input,
                collections=collections,
                top_n_each=5,
                top_n_total=10,
                content_type=selected_key
            )

            if "error" in result:
                response_text = f"API Error: {result['error']}"
                st.session_state.chat_history.append({"role": "bot", "content": response_text})
            else:
                results = result.get("results", [])
                if not results:
                    response_text = "🤷 No results found."
                    st.session_state.chat_history.append({"role": "bot", "content": response_text})
                else:
                    response_text = f"Found {len(results)} results for: *{user_input}*"
                    st.session_state.chat_history.append({"role": "bot", "content": response_text})

                    for i, item in enumerate(results, 1):
                        render_result(item)

# --- Display Chat Bubbles ---
for i, chat in enumerate(st.session_state.chat_history):
    is_user = chat["role"] == "user"
    message(chat["content"], is_user=is_user, key=f"{chat['role']}_{i}")
