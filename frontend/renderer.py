import streamlit as st

# PPT Rendering: An editable form for slide content.
# def render_ppt_editor(ppt_data, file_submit_callback):
#     st.subheader(f"📝 Edit Slides: {ppt_data.get('title', 'Untitled')}")
#     with st.form("ppt_edit_form"):
#         ppt_edits = {}

#         for i in range(1, 20):
#             heading_key = f"Slide{i}_Heading"
#             content_key = f"Slide{i}_Content"
            
#             heading = ppt_data.get(heading_key)
#             content = ppt_data.get(content_key)

#             if heading or content:
#                 st.markdown(f"#### Slide {i}")
#                 new_heading = st.text_input(f"Heading {i}", value=heading or "", key=f"ppt_heading_{i}")
#                 new_content = st.text_area(f"Content {i}", value=content or "", key=f"ppt_content_{i}")
#                 ppt_edits[heading_key] = new_heading
#                 ppt_edits[content_key] = new_content

#         submitted = st.form_submit_button("📤 Generate PPT")
#         if submitted:
#             st.write("📨 Submitting to API...")
#             file_submit_callback(ppt_edits)

# Blog Rendering: Convert blog content into Markdown.
def render_blog_as_markdown(blog_data):
    blog_md = f"### {blog_data.get('title', 'Untitled')}\n\n"
    for i in range(1, 20):  # assuming up to 20 sections
        subheading = blog_data.get(f"Subheading{i}")
        content = blog_data.get(f"Content{i}")
        if subheading and content:
            blog_md += f"#### {subheading}\n\n{content}\n\n"
    return blog_md

# Image Rendering
def render_image_result(result):
    payload = result.get("payload", {})
    file_id = payload.get("file_id", "N/A")
    description = payload.get("chunk_text", "No description available.")
    score = result.get("score", 0)
    image_url = payload.get("presigned_url")

    if image_url:
        with st.container():
            st.image(image_url, use_column_width=True, caption=description)
            with st.expander(f"📄 Details for {file_id}"):
                st.markdown(f"**File ID:** `{file_id}`")
                st.markdown(f"**Score:** `{score:.3f}`")
                st.markdown(f"**Description:** {description}")
                st.markdown(f"[🔗 Open Image in New Tab]({image_url})")
    else:
        st.warning(f"⚠️ Image URL not available for `{file_id}`.")

# JSON Rendering
def render_json_result(result):
    payload = result.get("payload", {})
    file_id = payload.get("file_id", "N/A")
    score = result.get("score", 0)

    with st.expander(f"🧾 JSON: {file_id} — Score: {score:.2f}"):
        editable_text = payload.get("chunk_text", "")
        
        # Editable text area for potential edits
        edited = st.text_area("✏️ Edit content:", editable_text, height=200)

        if st.button(f"Save Edits for {file_id}"):
            st.success("Saved (functionality to be implemented)")
            # Hook into your backend here

        st.markdown("#### 📦 Raw Payload Data")
        st.json(payload)

# Generic Rendering for any result
def render_result(result):
    payload = result.get("payload", {})
    source_type = payload.get("source_type", "")

    if source_type == "image" and payload.get("presigned_url"):
        render_image_result(result)
    else:
        render_json_result(result)
