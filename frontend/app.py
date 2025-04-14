import streamlit as st
from streamlit_chat import message
from services.api_client import search_data, generate_ppt_file, generate_pdf_file
from renderer import render_result, render_blog_as_markdown

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
    "Q&A": "text",
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
            
            # Map selected content type to collections (based on your backend design)
            collection_map = {
                "image": ["image"],
                "text": ["blog", "ppt", "pdf"],
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
                types=selected_key
            )
            
            if "error" in result:
                response_text = f"API Error: {result['error']}"
                st.session_state.chat_history.append({"role": "bot", "content": response_text})
            else:
                # Q&A block
                if selected_key == "text":
                    answer = result.get("generated_content", {}).get("text", {}).get("answer", "")
                    response_text = f"**Answer:** {answer}" if answer else "🤷 No answer found."
                    st.session_state.chat_history.append({"role": "bot", "content": response_text})
                
                # Blog block
                elif selected_key == "blog":
                    blog_data = result.get("generated_content", {}).get("text", {})
                    if blog_data:
                        markdown_content = render_blog_as_markdown(blog_data)
                        st.session_state.chat_history.append({"role": "bot", "content": markdown_content})
                    else:
                        st.session_state.chat_history.append({"role": "bot", "content": "🤷 No blog content found."})
                
                # PPT block
                elif selected_key == "ppt":
                    ppt_text_data = result.get("generated_content", {}).get("text", {})
                    if ppt_text_data:
                        with st.spinner("Generating PPT..."):
                            response = generate_ppt_file(ppt_text_data)
                        if "error" in response:
                            st.session_state.chat_history.append({
                                "role": "bot",
                                "content": f"Error generating presentation: {response['error']}"
                            })
                        else:
                            link = response.get("google_slides_link")
                            if link:
                                response_text = f"✅ Google Slides presentation generated! [Open Generated Slides]({link})"
                                st.session_state.chat_history.append({"role": "bot", "content": response_text})
                            else:
                                st.session_state.chat_history.append({
                                    "role": "bot",
                                    "content": "⚠️ No link returned from the PPT API."
                                })
                    else:
                        st.session_state.chat_history.append({"role": "bot", "content": "🤷 No PPT content found."})
                
                # PDF block
                elif selected_key == "pdf":
                    pdf_text_data = result.get("generated_content", {}).get("text", {})
                    if pdf_text_data:
                        with st.spinner("Generating PDF..."):
                            response = generate_pdf_file(pdf_text_data)
                        if "error" in response:
                            st.session_state.chat_history.append({
                                "role": "bot",
                                "content": f"Error generating document: {response['error']}"
                            })
                        else:
                            link = response.get("google_doc_link")
                            if link:
                                response_text = f"✅ Google Doc generated! [Open Document]({link})"
                                st.session_state.chat_history.append({"role": "bot", "content": response_text})
                            else:
                                st.session_state.chat_history.append({
                                    "role": "bot",
                                    "content": "⚠️ No link returned from the document generation API."
                                })
                    else:
                        st.session_state.chat_history.append({"role": "bot", "content": "🤷 No document content found."})
                
                # Images block
                elif selected_key == "image":
                    results = result.get("result_chunks", [])
                    if not results:
                        st.session_state.chat_history.append({"role": "bot", "content": "🤷 No images found."})
                    else:
                        # Append a quick summary
                        response_text = f"Found {len(results)} images for: *{user_input}*"
                        st.session_state.chat_history.append({"role": "bot", "content": response_text})

                        for i, item in enumerate(results, start=1):
                            payload = item.get("payload", {})
                            image_url = payload.get("presigned_url")
                            caption = payload.get("chunk_text", f"Image {i}")

                            if image_url:
                                # Construct an HTML snippet that forces the image to fit inside the chat bubble
                                image_html = f"""
                                <p><strong>Image {i}:</strong> {caption}</p>
                                <img src="{image_url}" alt="{caption}" 
                                    style="max-width: 100%; height: auto; display: block; margin: 0.5em 0;" />
                                """

                                # Mark that this message contains HTML
                                st.session_state.chat_history.append({
                                    "role": "bot",
                                    "content": image_html,
                                    "is_html": True
                                })
                            else:
                                st.session_state.chat_history.append({
                                    "role": "bot",
                                    "content": f"⚠️ Image URL not available for image {i}."
                                })

                
                # Default block for any other types
                else:
                    results = result.get("result_chunks", [])
                    if not results:
                        st.session_state.chat_history.append({"role": "bot", "content": "🤷 No results found."})
                    else:
                        response_text = f"Found {len(results)} results for: *{user_input}*"
                        st.session_state.chat_history.append({"role": "bot", "content": response_text})
                        for i, item in enumerate(results, 1):
                            st.session_state.chat_history.append({"role": "bot", "content": item.get("payload", {}).get("chunk_text", "Result")})

# --- Display Chat Bubbles ---
for i, chat in enumerate(st.session_state.chat_history):
    # Check if it's the user
    is_user = chat["role"] == "user"
    
    if "is_html" in chat and chat["is_html"] is True:
        # Instead of using message(), directly render HTML
        # so that it's not shown as raw text
        st.markdown(chat["content"], unsafe_allow_html=True)
    else:
        # Normal text message
        message(chat["content"], is_user=is_user, key=f"{chat['role']}_{i}")
