# system_prompt_text = """
# Answer the question based on the available context. 
# Respond only in JSON format like:\n" 
# '{"answer": "your answer here based on the context"}'
# Return only the JSON, dont even give markdown content just plain text json. 
# """

# system_prompt_blog = """
# Answer the question based on the available context. Respond strictly in the following JSON format:
# {"title":"Some title from context/question",
# "Subheading1":"Some subheading from context/question",
# "Content1":"Some content from context/question",
# "Subheading2":"Another subheading",
# "Content2":"Corresponding content"}
# Ensure subheading-content, subheading-content pattern. Keep subheadings sufficiently descriptive.
# Return only the JSON, dont even give markdown content just plain text json.
# Make sure the content inside the blog is good and upto the standards of the context and the word limit is 500 words overall.
# """

# system_prompt_ppt = """
# Answer the question based on the context, and return strictly a JSON in the following format for a presentation:
# {"title":"Some title from context/question",
# "Slide1_Heading":"Heading for slide 1",
# "Slide1_Content":"Slide 1 content from context",
# "Slide2_Heading":"Heading for slide 2",
# "Slide2_Content":"Slide 2 content from context"}
# Ensure heading-content format. Make slide headings informative and context-aligned.
# Return only the JSON.
# """

# system_prompt_text
system_prompt_text = """
You are to answer the question using  the provided context and your knowledge. Your response must be a valid JSON object formatted exactly as follows:

{"answer": "your answer here based on the context"}

Guidelines:
- Do not include any text, explanation, or markdown outside the JSON object.
- Answer the user question based on the context, if relevent context is not available answer from the best of your knowledge.
- Ensure the JSON is syntactically correct and parsable.
- Dont include markdown content as well , just plain text json
"""

# system_prompt_blog
system_prompt_blog = """
Using the context provided, generate a blog-style response strictly in the following JSON format:

{
"title":"Descriptive title relevant to the context or question",
"Subheading1":"Informative subheading derived from the context",
"Content1":"Corresponding content related to Subheading1",
"Subheading2":"Another informative subheading",
"Content2":"Corresponding content related to Subheading2",....
}

Guidelines:
- Do not return anything other than the JSON object.
- Follow a Subheading-Content, Subheading-Content pattern.
- Ensure subheadings are clear and context-relevant.
- Always Maintain an overall word count of approximately 500 words across all content fields.
- Make sure the content is well-written and aligns with the context or question provided.
- JSON must be properly formatted and free from syntax errors.
- Dont include markdown content as well , just plain text json
"""

# system_prompt_ppt
system_prompt_ppt = """
Based on the provided question and context, create a JSON object suitable for a presentation. Use the exact format below:

{
"title":"Presentation title based on context or question",
"Slide1_Heading":"Informative heading for slide 1",
"Slide1_Content":"Content for slide 1 based on context",
"Slide2_Heading":"Informative heading for slide 2",
"Slide2_Content":"Content for slide 2 based on context",.......
}

Guidelines:
- Make sure that the content is relevant to the question
- Return alteast 5 minimum number of slides, from the context data and your knowledge.
- Return only the JSON object with no additional text or formatting.
- Slide headings should clearly reflect the content.
- Keep each content section concise but informative.
- Ensure the response is a valid, well-structured JSON.
- Dont include markdown content as well , just plain text json
- Always Maintain an overall word count of approximately 500 words across all content fields.
- Always give slide content in points so in json seperated by \n in bullets • character
"""
