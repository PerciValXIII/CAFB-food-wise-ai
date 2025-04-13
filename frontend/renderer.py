import streamlit as st

def render_image_result(result):
    payload = result.get("payload", {})
    file_id = payload.get("file_id", "N/A")
    description = payload.get("chunk_text", "No description available.")
    score = result.get("score", 0)
    image_url = payload.get("presigned_url")

    with st.expander(f"🖼️ {file_id} — Score: {score:.2f}"):
        if image_url:
            st.image(image_url, use_column_width=True)
        st.markdown(f"📝 {description}")


def render_json_result(result):
    payload = result.get("payload", {})
    file_id = payload.get("file_id", "N/A")
    score = result.get("score", 0)

    with st.expander(f"🧾 JSON: {file_id} — Score: {score:.2f}"):
        editable_text = payload.get("chunk_text", "")
        
        # Editable text area
        edited = st.text_area("✏️ Edit content:", editable_text, height=200)

        # Save/submit button
        if st.button(f"Save Edits for {file_id}"):
            st.success("Saved (functionality to be implemented)")
            # Hook into your backend here

        # 🔄 Just show raw JSON without nesting another expander
        st.markdown("#### 📦 Raw Payload Data")
        st.json(payload)

        

def render_result(result):
    payload = result.get("payload", {})
    source_type = payload.get("source_type")

    if source_type == "image" and payload.get("presigned_url"):
        render_image_result(result)
    else:
        render_json_result(result)