import streamlit as st
from streamlit_chat import message
from services.api_client import search_data

st.set_page_config(page_title="FoodWise AI Assistant", layout="wide")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("FoodWise Chatbot")
st.markdown("Ask me something and I’ll search for matching images from the knowledge base.")

# Sidebar for file uploads (optional for future use)
st.sidebar.header("Upload Files")
uploaded_files = st.sidebar.file_uploader(
    "Drag and drop files here", accept_multiple_files=True
)

# Chat input
user_input = st.chat_input("Type your query here...")

# Handle user input
if user_input:
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Call API and get result
    with st.spinner("Searching for results..."):
        result = search_data(user_input, collections=["image"])

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

                # Display each result in an expandable card
                for i, item in enumerate(results, 1):
                    payload = item.get("payload", {})
                    file_id = payload.get("file_id", "N/A")
                    description = payload.get("chunk_text", "No description available.")
                    score = item.get("score", 0)
                    image_url = payload.get("presigned_url")

                    with st.expander(f"{i}. {file_id} — Score: {score:.2f}"):
                        if image_url:
                            st.image(image_url, use_column_width=True)
                        st.markdown(f"{description}")

# Display full chat history in bubbles
for i, chat in enumerate(st.session_state.chat_history):
    is_user = chat["role"] == "user"
    message(chat["content"], is_user=is_user, key=f"{chat['role']}_{i}")
