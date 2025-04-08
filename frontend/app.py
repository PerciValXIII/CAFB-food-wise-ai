import streamlit as st
from streamlit_chat import message
from frontend.services.api_client import search_data

st.set_page_config(page_title="FoodWise AI Assistant", layout="wide")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("FoodWise Chatbot")
st.markdown("Ask me something and I’ll pull from the knowledge base.")

# Sidebar for file uploads (can be expanded later)
st.sidebar.header("Upload Files")
uploaded_files = st.sidebar.file_uploader(
    "Drag and drop files here", accept_multiple_files=True
)

# Chat input
user_input = st.chat_input("Type your query here...")

# User types a query
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # 🔄 Call API and handle response
    with st.spinner("Fetching results from backend..."):
        result = search_data(user_input, collections=["image"])

        if "error" in result:
            response_text = f"⚠️ API Error: {result['error']}"
        else:
            results = result.get("results", [])
            if not results:
                response_text = "🤷 No results found."
            else:
                response_text = "🔍 **Top Results:**\n\n"
                for i, item in enumerate(results, 1):
                    payload = item.get("payload", {})
                    file_id = payload.get("file_id", "N/A")
                    description = payload.get("chunk_text", "No description available.")
                    score = item.get("score", 0)

                    response_text += (
                        f"**{i}. File:** `{file_id}`\n"
                        f"📝 *{description}*\n"
                        f"🎯 Score: `{score:.2f}`\n\n"
                    )

    # Add assistant response
    st.session_state.chat_history.append({"role": "bot", "content": response_text})

# Display chat history
for i, chat in enumerate(st.session_state.chat_history):
    is_user = chat["role"] == "user"
    message(chat["content"], is_user=is_user, key=f"{chat['role']}_{i}")
