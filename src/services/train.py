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

def train_ppt(db):
    create_text_collection_if_not_exists("ppt")
    ppt_untrained = db.query(PptData).filter(PptData.train == False).order_by(PptData.id).all()
    if ppt_untrained:
        print(f"Found {len(ppt_untrained)} untrained PPT rows.")
        grouped_slides = defaultdict(list)
        for doc in ppt_untrained:
            grouped_slides[doc.file_id].append(doc)

        for file_id, docs in grouped_slides.items():
            try:
                all_texts = []
                for doc in docs:
                    content_json = json.loads(doc.content_json) if isinstance(doc.content_json, str) else doc.content_json
                    slide_title = content_json.get("slide_title", "")
                    content_items = content_json.get("content", [])
                    texts = [item.get("text", "") for item in content_items]
                    full_text = f"{slide_title}\n" + "\n".join(texts).strip()
                    if full_text:
                        all_texts.append(full_text)

                combined_text = "\n---\n".join(all_texts).strip()
                if not combined_text:
                    continue

                print(f"Training PPT file: {file_id} with {len(docs)} slides.")
                embedding_resp = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=combined_text,
                    encoding_format="float"
                )
                embedding = embedding_resp.data[0].embedding

                payload = {
                    "id": docs[0].id,
                    "source_type": "ppt",
                    "file_id": file_id,
                    "file_name": docs[0].file_name,
                    "chunk_text": combined_text,
                    "slide_count": len(docs)
                }
                point_id = uuid.uuid4().hex
                qdrant_client.upsert(collection_name="ppt", points=[PointStruct(id=point_id, vector=embedding, payload=payload)])

                for doc in docs:
                    doc.train = True

            except Exception as ppt_err:
                print(f"Skipping PPT file_id {file_id} due to error: {ppt_err}")

        print("PPT training complete.")
    else:
        print("No untrained PPT data found.")

def train_pdf(db):
    create_text_collection_if_not_exists("pdf")
    pdf_untrained = db.query(PdfData).filter(PdfData.train == False).order_by(PdfData.id).all()
    if pdf_untrained:
        print(f"Found {len(pdf_untrained)} untrained PDF rows.")
        for doc in pdf_untrained:
            try:
                content_json = json.loads(doc.content_json) if isinstance(doc.content_json, str) else doc.content_json
                slide_title = content_json.get("slide_title", "")
                content_items = content_json.get("content", [])
                texts = [item.get("text", "") for item in content_items]
                full_text = f"{slide_title}\n" + "\n".join(texts).strip()
                if not full_text:
                    continue

                print(f"Training PDF: {doc.file_id} (Doc ID {doc.id})")
                embedding_resp = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=full_text,
                    encoding_format="float"
                )
                embedding = embedding_resp.data[0].embedding

                payload = {
                    "id": doc.id,
                    "source_type": "pdf",
                    "file_id": doc.file_id,
                    "file_name": doc.file_name,
                    "chunk_text": full_text
                }
                point_id = uuid.uuid4().hex
                qdrant_client.upsert(collection_name="pdf", points=[PointStruct(id=point_id, vector=embedding, payload=payload)])

                doc.train = True

            except Exception as pdf_err:
                print(f"Skipping PDF doc ID {doc.id} due to error: {pdf_err}")

        print("PDF training complete.")
    else:
        print("No untrained PDF data found.")


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