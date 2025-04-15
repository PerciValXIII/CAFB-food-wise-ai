import uuid
import json
from collections import defaultdict
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from src.services.table_classes import *
from openai import OpenAI
# Initialize Qdrant Client

qdrant_url=os.getenv("QDRANT_URL")
api_qdrant=os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
qdrant_client = QdrantClient(
    url = qdrant_url,
    api_key= api_qdrant
)
client = OpenAI(api_key=OPENAI_API_KEY)
# Create collection if not exists
def create_text_collection_if_not_exists(COLLECTION_NAME):
    """Creates the Qdrant collection if it does not already exist."""
    existing_collections = qdrant_client.get_collections().collections
    if any(col.name == COLLECTION_NAME for col in existing_collections):
        print(f"Collection '{COLLECTION_NAME}' already exists.")
        return
    print(f"Creating collection: {COLLECTION_NAME}")
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=1536,  # dimension for 'text-embedding-3-small'
            distance=Distance.COSINE
        )
    )

def train_blog(db):
    create_text_collection_if_not_exists("blog")
    blog_untrained = db.query(BlogData).filter(BlogData.train == False).order_by(BlogData.id).all()
    if blog_untrained:
        print(f"Found {len(blog_untrained)} untrained blog rows.")
        blog_points = []
        for doc in blog_untrained:
            text_for_embedding = doc.content if doc.content else ""
            print(f"Training Blog: {doc.file_id} (ID {doc.id})")
            embedding_resp = client.embeddings.create(
                model="text-embedding-3-small",
                input=text_for_embedding,
                encoding_format="float"
            )
            embedding = embedding_resp.data[0].embedding
            payload = {
                "id": doc.id,
                "source_type": "blog",
                "file_id": doc.file_id,
                "file_name": doc.file_name,
                "chunk_text": doc.content,
                "url": doc.url
            }
            point_id = uuid.uuid4().hex
            point = PointStruct(id=point_id, vector=embedding, payload=payload)
            doc.train = True
            qdrant_client.upsert(collection_name="blog", points=[point])
        print("Blog training complete.")
    else:
        print("No untrained Blog data found.")

# def train_ppt(db):
#     create_text_collection_if_not_exists("ppt")
#     ppt_untrained = db.query(PptData).filter(PptData.train == False).order_by(PptData.id).all()
#     if ppt_untrained:
#         print(f"Found {len(ppt_untrained)} untrained PPT rows.")
#         grouped_slides = defaultdict(list)
#         for doc in ppt_untrained:
#             grouped_slides[doc.file_id].append(doc)

#         for file_id, docs in grouped_slides.items():
#             try:
#                 all_texts = []
#                 for doc in docs:
#                     content_json = json.loads(doc.content_json) if isinstance(doc.content_json, str) else doc.content_json
#                     slide_title = content_json.get("slide_title", "")
#                     content_items = content_json.get("content", [])
#                     texts = [item.get("text", "") for item in content_items]
#                     full_text = f"{slide_title}\n" + "\n".join(texts).strip()
#                     if full_text:
#                         all_texts.append(full_text)

#                 combined_text = "\n---\n".join(all_texts).strip()
#                 if not combined_text:
#                     continue

#                 print(f"Training PPT file: {file_id} with {len(docs)} slides.")
#                 embedding_resp = client.embeddings.create(
#                     model="text-embedding-3-small",
#                     input=combined_text,
#                     encoding_format="float"
#                 )
#                 embedding = embedding_resp.data[0].embedding

#                 payload = {
#                     "id": docs[0].id,
#                     "source_type": "ppt",
#                     "file_id": file_id,
#                     "file_name": docs[0].file_name,
#                     "chunk_text": combined_text,
#                     "slide_count": len(docs)
#                 }
#                 point_id = uuid.uuid4().hex
#                 qdrant_client.upsert(collection_name="ppt", points=[PointStruct(id=point_id, vector=embedding, payload=payload)])

#                 for doc in docs:
#                     doc.train = True

#             except Exception as ppt_err:
#                 print(f"Skipping PPT file_id {file_id} due to error: {ppt_err}")

#         print("PPT training complete.")
#     else:
#         print("No untrained PPT data found.")

# def train_pdf(db):
#     create_text_collection_if_not_exists("pdf")
#     pdf_untrained = db.query(PdfData).filter(PdfData.train == False).order_by(PdfData.id).all()
#     if pdf_untrained:
#         print(f"Found {len(pdf_untrained)} untrained PDF rows.")
#         for doc in pdf_untrained:
#             try:
#                 content_json = json.loads(doc.content_json) if isinstance(doc.content_json, str) else doc.content_json
#                 slide_title = content_json.get("slide_title", "")
#                 content_items = content_json.get("content", [])
#                 texts = [item.get("text", "") for item in content_items]
#                 full_text = f"{slide_title}\n" + "\n".join(texts).strip()
#                 if not full_text:
#                     continue

#                 print(f"Training PDF: {doc.file_id} (Doc ID {doc.id})")
#                 embedding_resp = client.embeddings.create(
#                     model="text-embedding-3-small",
#                     input=full_text,
#                     encoding_format="float"
#                 )
#                 embedding = embedding_resp.data[0].embedding

#                 payload = {
#                     "id": doc.id,
#                     "source_type": "pdf",
#                     "file_id": doc.file_id,
#                     "file_name": doc.file_name,
#                     "chunk_text": full_text
#                 }
#                 point_id = uuid.uuid4().hex
#                 qdrant_client.upsert(collection_name="pdf", points=[PointStruct(id=point_id, vector=embedding, payload=payload)])

#                 doc.train = True

#             except Exception as pdf_err:
#                 print(f"Skipping PDF doc ID {doc.id} due to error: {pdf_err}")

#         print("PDF training complete.")
#     else:
#         print("No untrained PDF data found.")


def train_image(db):
    create_text_collection_if_not_exists("image")
    image_untrained = db.query(Image).filter(Image.train == False).order_by(Image.id).all()
    if image_untrained:
        print(f"Found {len(image_untrained)} untrained blog rows.")
        blog_points = []
        for image in image_untrained:
            text_for_embedding = image.content if image.content else ""
            print("text_for_embedding ",text_for_embedding)
            print(f"Training Blog: {image.image_id} (ID {image.id})")
            embedding_resp = client.embeddings.create(
                model="text-embedding-3-small",
                input=text_for_embedding,
                encoding_format="float"
            )
            print("embeddings done")
            embedding = embedding_resp.data[0].embedding
            payload = {
                "id": image.id,
                "source_type": "image",
                "file_id": image.image_id,
                "chunk_text": image.content
            }
            point_id = uuid.uuid4().hex
            point = PointStruct(id=point_id, vector=embedding, payload=payload)
            image.train = True
            print("qdrant started")
            qdrant_client.upsert(collection_name="image", points=[point])
            db.commit()
        print("Image training complete.")
    else:
        print("No untrained Image data found.")


# def train_ppt_chunk(db):
#     create_text_collection_if_not_exists("ppt_chunk")
#     ppt_untrained = db.query(PptData).filter(PptData.train == False).order_by(PptData.id).all()
#     if ppt_untrained:
#         print(f"Found {len(ppt_untrained)} untrained PPT rows.")
        
#         from collections import defaultdict
#         grouped_slides = defaultdict(list)
#         for doc in ppt_untrained:
#             grouped_slides[doc.file_id].append(doc)

#         for file_id, docs in grouped_slides.items():
#             print(f"Processing PPT file_id: {file_id} with {len(docs)} slides.")
#             for doc in docs:
#                 try:
#                     # Load content JSON
#                     content_json = (
#                         json.loads(doc.content_json)
#                         if isinstance(doc.content_json, str)
#                         else doc.content_json
#                     )
                    
#                     # Extract fields from the JSON
#                     slide_filename  = content_json.get("filename", "")
#                     slide_number    = content_json.get("slide_number", "")
#                     slide_title     = content_json.get("slide_title", "")
#                     content_items   = content_json.get("content", [])

#                     chunk_text =""
#                     # For PPT slides, chunk each piece of text separately
#                     for idx, item in enumerate(content_items):
#                         chunk_text += item.get("text", "").strip()
#                         if not chunk_text:
#                             continue

#                     # Optionally prepend slide title to each chunk
#                     chunk_text = f"{slide_title}\n{chunk_text}".strip()

#                     # Create embedding for this chunk
#                     embedding_resp = client.embeddings.create(
#                         model="text-embedding-3-small",
#                         input=chunk_text,
#                         encoding_format="float"
#                     )
#                     embedding = embedding_resp.data[0].embedding

#                     # Build payload for Qdrant
#                     payload = {
#                         "id": doc.id,                # PptData record ID
#                         "source_type": "ppt",
#                         "file_id": doc.file_id,       # DB-level file_id
#                         "file_name": doc.file_name,   # or slide_filename (if they differ)
#                         "slide_filename": slide_filename,
#                         "slide_number": slide_number,
#                         "slide_title": slide_title,
#                         "chunk_text": chunk_text,
#                         "content_index": idx
#                     }

#                     point_id = uuid.uuid4().hex
#                     qdrant_client.upsert(
#                         collection_name="ppt_chunk",
#                         points=[PointStruct(id=point_id, vector=embedding, payload=payload)]
#                     )

#                     # Mark this row (slide) as trained after all chunks processed
#                     doc.train = True
#                     db.commit()

#                 except Exception as ppt_err:
#                     print(f"Skipping PPT file_id {file_id}, doc ID {doc.id} due to error: {ppt_err}")

#         print("PPT training complete.")
#     else:
#         print("No untrained PPT data found.")



# def train_pdf_chunk(db):
#     create_text_collection_if_not_exists("pdf_chunk")
#     pdf_untrained = db.query(PdfData).filter(PdfData.train == False).order_by(PdfData.id).all()
#     if pdf_untrained:
#         print(f"Found {len(pdf_untrained)} untrained PDF rows.")
#         for doc in pdf_untrained:
#             try:
#                 # Load content JSON
#                 content_json = (
#                     json.loads(doc.content_json)
#                     if isinstance(doc.content_json, str)
#                     else doc.content_json
#                 )
#                 file_id = content_json.get("file_id", "")
#                 filename = content_json.get("filename", "")
#                 content_items = content_json.get("content", [])

#                 # For each content chunk (page/paragraph), embed and upsert separately
#                 for idx, item in enumerate(content_items):
#                     page_num = item.get("page")
#                     paragraph_num = item.get("paragraph")
#                     chunk_text = item.get("text", "").strip()
#                     if not chunk_text:
#                         continue

#                     # Create embedding
#                     embedding_resp = client.embeddings.create(  
#                         model="text-embedding-3-small",
#                         input=chunk_text,
#                         encoding_format="float"
#                     )
#                     embedding = embedding_resp.data[0].embedding

#                     # Build payload with relevant metadata
#                     payload = {
#                         "id": doc.id,           
#                         "source_type": "pdf",
#                         "file_id": file_id,
#                         "file_name": filename,
#                         "chunk_text": chunk_text,
#                         "page": page_num,
#                         "paragraph": paragraph_num,
#                         "content_index": idx
#                     }

#                     # Upsert this chunk into Qdrant
#                     point_id = uuid.uuid4().hex
#                     qdrant_client.upsert(
#                         collection_name="pdf_chunk",
#                         points=[PointStruct(id=point_id, vector=embedding, payload=payload)]
#                     )

#                 # Mark the doc as trained after processing all chunks
#                 doc.train = True
#                 db.commit()

#             except Exception as pdf_err:
#                 print(f"Skipping PDF doc ID {doc.id} due to error: {pdf_err}")

#         print("PDF training complete.")
#     else:
#         print("No untrained PDF data found.")

def train_ppt(db):
    """
    Combines file-level training (all slides in a PPT as one embedding) 
    and slide/chunk-level training (each slide individually) for all
    untrained PPT data. 
    Stores file-level embeddings in the 'ppt' collection, 
    and slide/chunk-level embeddings in the 'ppt_chunk' collection.
    """
    # Make sure both collections exist
    create_text_collection_if_not_exists("ppt")
    create_text_collection_if_not_exists("ppt_chunk")

    from collections import defaultdict

    # Fetch untrained PPT data
    ppt_untrained = (
        db.query(PptData)
        .filter(PptData.train == False)
        .order_by(PptData.id)
        .all()
    )
    if not ppt_untrained:
        print("No untrained PPT data found.")
        return

    print(f"Found {len(ppt_untrained)} untrained PPT rows.")

    # -- 1) File-level training for PPT documents --
    # Group all PPT slides by file_id so we can create one combined embedding per file
    grouped_slides = defaultdict(list)
    for doc in ppt_untrained:
        grouped_slides[doc.file_id].append(doc)

    for file_id, docs in grouped_slides.items():
        try:
            # Gather all text from the slides in this file
            all_texts = []
            for doc in docs:
                content_json = (
                    json.loads(doc.content_json)
                    if isinstance(doc.content_json, str)
                    else doc.content_json
                )
                slide_title = content_json.get("slide_title", "")
                content_items = content_json.get("content", [])
                slide_texts = [item.get("text", "") for item in content_items]
                full_text = f"{slide_title}\n" + "\n".join(slide_texts).strip()
                if full_text:
                    all_texts.append(full_text)

            # Combine into one text blob for the entire file
            combined_text = "\n---\n".join(all_texts).strip()
            if not combined_text:
                continue

            print(f"Training PPT file-level for file_id={file_id} with {len(docs)} slides.")

            # Create a single embedding for the entire file
            embedding_resp = client.embeddings.create(
                model="text-embedding-3-small",
                input=combined_text,
                encoding_format="float"
            )
            embedding = embedding_resp.data[0].embedding

            # Upsert into 'ppt' collection
            payload = {
                "id": docs[0].id,           # or any representative doc ID
                "source_type": "ppt",
                "file_id": file_id,
                "file_name": docs[0].file_name,
                "chunk_text": combined_text,
                "slide_count": len(docs)
            }
            point_id = uuid.uuid4().hex
            qdrant_client.upsert(
                collection_name="ppt",
                points=[
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )

        except Exception as ppt_err:
            print(f"[FILE-LEVEL] Skipping PPT file_id={file_id} due to error: {ppt_err}")
            # Continue to next file_id
            continue

    # -- 2) Slide/chunk-level training for PPT documents --
    print("Starting chunk-level training for PPT slides...")

    # Re-group (since we still need to embed each doc individually)
    # Alternatively, you could reuse the grouped_slides from above.
    grouped_slides_for_chunks = defaultdict(list)
    for doc in ppt_untrained:
        grouped_slides_for_chunks[doc.file_id].append(doc)

    for file_id, docs in grouped_slides_for_chunks.items():
        print(f"Processing PPT file_id: {file_id} with {len(docs)} slides (chunk-level).")
        for doc in docs:
            try:
                content_json = (
                    json.loads(doc.content_json)
                    if isinstance(doc.content_json, str)
                    else doc.content_json
                )
                slide_filename = content_json.get("filename", "")
                slide_number = content_json.get("slide_number", "")
                slide_title = content_json.get("slide_title", "")
                content_items = content_json.get("content", [])

                # For chunk-level, you might chunk each slide piece or treat the entire slide as one chunk
                chunk_text = ""
                for idx, item in enumerate(content_items):
                    chunk_text = item.get("text", "").strip()
                    if not chunk_text:
                        continue

                    # Optionally prepend the slide title
                    text_for_embedding = f"{slide_title}\n{chunk_text}".strip()

                    # Embed
                    embedding_resp = client.embeddings.create(
                        model="text-embedding-3-small",
                        input=text_for_embedding,
                        encoding_format="float"
                    )
                    embedding = embedding_resp.data[0].embedding

                    # Prepare payload
                    payload = {
                        "id": doc.id,  # PptData record ID
                        "source_type": "ppt",
                        "file_id": doc.file_id,
                        "file_name": doc.file_name,
                        "slide_filename": slide_filename,
                        "slide_number": slide_number,
                        "slide_title": slide_title,
                        "chunk_text": text_for_embedding,
                        "content_index": idx
                    }

                    point_id = uuid.uuid4().hex
                    qdrant_client.upsert(
                        collection_name="ppt_chunk",
                        points=[
                            PointStruct(
                                id=point_id,
                                vector=embedding,
                                payload=payload
                            )
                        ]
                    )

                # Mark this slide as trained
                doc.train = True
                db.commit()

            except Exception as ppt_err:
                print(f"[CHUNK-LEVEL] Skipping PPT file_id={file_id}, doc ID={doc.id} due to error: {ppt_err}")

    print("PPT training (file-level + chunk-level) complete.")


def train_pdf(db):
    """
    Combines file-level training (entire PDF as one embedding) 
    and chunk-level training (per page/paragraph) for all untrained PDF data.
    Stores file-level embeddings in the 'pdf' collection, 
    and chunk-level embeddings in the 'pdf_chunk' collection.
    """
    # Ensure both collections exist
    create_text_collection_if_not_exists("pdf")
    create_text_collection_if_not_exists("pdf_chunk")

    # Fetch untrained PDF data
    pdf_untrained = (
        db.query(PdfData)
        .filter(PdfData.train == False)
        .order_by(PdfData.id)
        .all()
    )
    if not pdf_untrained:
        print("No untrained PDF data found.")
        return

    print(f"Found {len(pdf_untrained)} untrained PDF rows.")

    # -- 1) File-level training (combine all text in a single PDF) --
    # The simplest approach is to group by file_id if multiple DB rows belong to the same PDF:
    from collections import defaultdict
    grouped_pdfs = defaultdict(list)
    for doc in pdf_untrained:
        # Your schema might put the same PDF content in multiple rows, 
        # or each doc is truly a separate PDF. Adjust accordingly.
        grouped_pdfs[doc.file_id].append(doc)

    for file_id, docs in grouped_pdfs.items():
        try:
            # Combine all text from these docs into one big string
            all_texts = []
            for doc in docs:
                content_json = (
                    json.loads(doc.content_json)
                    if isinstance(doc.content_json, str)
                    else doc.content_json
                )
                slide_title = content_json.get("slide_title", "")
                content_items = content_json.get("content", [])
                texts = [item.get("text", "") for item in content_items]
                full_text = f"{slide_title}\n" + "\n".join(texts).strip()
                if full_text:
                    all_texts.append(full_text)

            combined_text = "\n---\n".join(all_texts).strip()
            if not combined_text:
                continue

            print(f"Training PDF file-level for file_id={file_id} with {len(docs)} doc rows.")
            # Embed
            embedding_resp = client.embeddings.create(
                model="text-embedding-3-small",
                input=combined_text,
                encoding_format="float"
            )
            embedding = embedding_resp.data[0].embedding

            # Upsert to 'pdf' collection
            payload = {
                "id": docs[0].id,  # or any doc's ID
                "source_type": "pdf",
                "file_id": file_id,
                "file_name": docs[0].file_name,
                "chunk_text": combined_text
            }
            point_id = uuid.uuid4().hex
            qdrant_client.upsert(
                collection_name="pdf",
                points=[PointStruct(id=point_id, vector=embedding, payload=payload)]
            )
        except Exception as pdf_err:
            print(f"[FILE-LEVEL] Skipping PDF file_id={file_id} due to error: {pdf_err}")
            continue

    # -- 2) Chunk-level training (page or paragraph chunks) --
    print("Starting chunk-level training for PDFs...")

    for doc in pdf_untrained:
        try:
            content_json = (
                json.loads(doc.content_json)
                if isinstance(doc.content_json, str)
                else doc.content_json
            )
            file_id = content_json.get("file_id", doc.file_id)  # fallback to DB field if needed
            filename = content_json.get("filename", doc.file_name)
            content_items = content_json.get("content", [])

            for idx, item in enumerate(content_items):
                page_num = item.get("page")
                paragraph_num = item.get("paragraph")
                chunk_text = item.get("text", "").strip()
                if not chunk_text:
                    continue

                # Embed
                embedding_resp = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=chunk_text,
                    encoding_format="float"
                )
                embedding = embedding_resp.data[0].embedding

                # Upsert to 'pdf_chunk' collection
                payload = {
                    "id": doc.id,
                    "source_type": "pdf",
                    "file_id": file_id,
                    "file_name": filename,
                    "chunk_text": chunk_text,
                    "page": page_num,
                    "paragraph": paragraph_num,
                    "content_index": idx
                }
                point_id = uuid.uuid4().hex
                qdrant_client.upsert(
                    collection_name="pdf_chunk",
                    points=[PointStruct(id=point_id, vector=embedding, payload=payload)]
                )

            # Mark entire doc as trained
            doc.train = True
            db.commit()

        except Exception as pdf_err:
            print(f"[CHUNK-LEVEL] Skipping PDF doc ID={doc.id} due to error: {pdf_err}")

    print("PDF training (file-level + chunk-level) complete.")
