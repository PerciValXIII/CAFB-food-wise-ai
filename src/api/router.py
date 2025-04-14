from fastapi import HTTPException, File, UploadFile, APIRouter, Depends, Response,Body
from dotenv import load_dotenv
import json
import requests
import base64
import shutil
#from docx import Document
import ast
from typing import Generator
import tempfile
from datetime import datetime
import numpy as np
from typing import List
# from src.services.logging import log_api_event
from src.services.utils import *
from src.services.table_classes import *
from src.services.train import *
from src.services.schema import *
from src.services.backup import *
from src.services.google_slides import *
from src.services.google_docs import *
from src.services.s3_handler import S3Handler
from sqlalchemy import func
from typing import Optional,Union
import zipfile
from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
import io
import re
from tempfile import SpooledTemporaryFile
import uuid
load_dotenv()
from auth import verify_token
import traceback
# Initialize FastAPI app
app = APIRouter()

#create S3 handler object
s3_handler = S3Handler(aws_access_key_id=os.getenv("AWS_ACCESS_KEY"), aws_secret_access_key=os.getenv("AWS_SECRET_KEY"), region_name=os.getenv("AWS_REGION"))


# Endpoint for API 1: Convert image to text using LLM and generate request ID
@app.post("/user/signup", tags=["Users"])
def sign_up(user_info: SignupSchema, db: Session = Depends(get_db),token: str = Depends(verify_token)):
    try:
        user_data = user_info.dict()
        existing_user = db.query(Users).filter(Users.email == user_data['email']).filter(Users.password == user_data['password']).first()
        if existing_user:
            response = ResponseModel(status_code=500 ,message="User already registered")
            return response

        print("user_data",user_data)
        result = Users(**user_data)
        print("result",result)
        db.add(result)
        db.commit()
        response= ResponseModel(message="Sign up successful")
        return response
    except HTTPException as e:
        print(e)
        raise 
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Sign up failed")

@app.post("/user/login", tags=["Users"])
def login(user_info: LoginSchema, db: Session = Depends(get_db),token: str = Depends(verify_token)):
    try:
        user_info = user_info.dict()
        email = user_info['email']
        password = user_info['password']
        
        # Check if the user exists
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            response = ResponseModel(message="User does not exist")
            raise HTTPException(status_code=500, detail="User does not exist")
        if user.password != password:
           response = ResponseModel(message="Invalid credentials")
           raise HTTPException(status_code=500, detail="Invalid credentials")
        response = ResponseModel(message="Login successful", payload={"user_id": user.id, "role": user.role})
        return response
    
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Login failed")
    
@app.post("/data/train", tags=["Train"])
def train(db: Session = Depends(get_db),token: str = Depends(verify_token)):
    try:
        train_blog(db)
        train_ppt(db)
        train_pdf(db)
        train_image(db)
        db.commit()
        return ResponseModel(message="Training complete.")#{"status": "success", "message": "Training complete."}   
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Train failed")


# @app.post("/data/search", tags=["Search"])
# def search_similar_documents(
#     req: SearchRequest,
#     db: Session = Depends(get_db),
#     token: str = Depends(verify_token)
# ):
#     try:
#         # Step 1: Convert input query to embeddings
#         embedding_resp = client.embeddings.create(
#             model="text-embedding-3-small",
#             input=req.query,
#             encoding_format="float"
#         )
#         embedding = embedding_resp.data[0].embedding

#         # Initialize S3
#         s3_handler.connect()
#         print("connected")

#         BUCKET_NAME = "cfab"

#         # Step 2: Search in each collection and gather top results
#         all_results = []
#         for collection in req.collections:
#             if collection in ["ppt", "pdf", "blog", "image", "pdf_chunk", "ppt_chunk"]:
#                 try:
#                     result = qdrant_client.search(
#                         collection_name=collection,
#                         query_vector=embedding,
#                         limit=req.top_n_each
#                     )

#                     # Add S3 URL to payload if applicable
#                     for item in result:
#                         payload = item.payload
#                         if "source_type" in payload and "file_id" in payload:
#                             source_type = payload["source_type"]

#                             # Determine content type
#                             if source_type == "image":
#                                 file_name = "images/"+ payload["file_id"]
#                                 content_type = "image/png"
#                             elif source_type == "pdf":
#                                 file_name = "on_premise_data/collateral/"+payload["file_name"]
#                                 content_type = "application/pdf"
#                             elif source_type == "ppt":
#                                 file_name = "on_premise_data/powerpoints/"+payload["file_name"]
#                                 content_type = "application/vnd.ms-powerpoint"
#                             else:
#                                 content_type = "application/octet-stream"
#                                 continue

#                             # Create presigned URL
#                             presigned_url = s3_handler.create_presigned_url(
#                                 bucket_name=BUCKET_NAME,
#                                 object_name=file_name,
#                                 expiration=60 * 5,  # 5 minutes
#                                 content_type=content_type
#                             )


#                             # Attach to payload
#                             item.payload["presigned_url"] = presigned_url

#                     all_results.extend(result)

#                 except Exception as e:
#                     print(e)
#             else:
#                 return ResponseModel(message=f"The collection {collection} is not found in the vector DB")

#         all_results.sort(key=lambda x: x.score, reverse=True)
#         return {"status": "success", "results": all_results[:req.top_n_total]}

#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         print(e)
#         raise HTTPException(status_code=500, detail="Similarity search failed.")


# @app.post("/data/predict", tags=["Predict"])
# def train(user_prompt:str,system_prompt:str,model: Optional[str] = "gpt-4o-mini", db: Session = Depends(get_db),token: str = Depends(verify_token)):
#     try:
#         output = simple_gpt(user_prompt,system_prompt,model)
#         return ResponseModel(message="Answer generated",payload={"content":output})#{"status": "success", "message": "Training complete."}   
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         print(e)
#         raise HTTPException(status_code=500, detail="Generation failed")




@app.post("/data/search", tags=["Search"])
def search_similar_documents(
    req: SearchRequest,
    db: Session = Depends(get_db),
    token: str = Depends(verify_token)
):
    try:
        # Step 1: Convert input query to embeddings
        embedding_resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=req.query,
            encoding_format="float"
        )
        embedding = embedding_resp.data[0].embedding

        # Step 2: Initialize S3
        s3_handler.connect()
        print("connected")

        BUCKET_NAME = "cfab"

        # Step 3: Search in each collection and gather top results
        all_results = []
        for collection in req.collections:
            if collection in ["ppt", "pdf", "blog", "image", "pdf_chunk", "ppt_chunk"]:
                try:
                    result = qdrant_client.search(
                        collection_name=collection,
                        query_vector=embedding,
                        limit=req.top_n_each
                    )

                    # Add S3 URL to payload if applicable
                    for item in result:
                        payload = item.payload
                        if "source_type" in payload and "file_id" in payload:
                            source_type = payload["source_type"]

                            # Determine content type
                            if source_type == "image":
                                file_name = "images/" + payload["file_id"]
                                content_type = "image/png"
                            elif source_type == "pdf":
                                file_name = "on_premise_data/collateral/" + payload["file_name"]
                                content_type = "application/pdf"
                            elif source_type == "ppt":
                                file_name = "on_premise_data/powerpoints/" + payload["file_name"]
                                content_type = "application/vnd.ms-powerpoint"
                            else:
                                # If not recognized, skip presigned URL generation
                                continue

                            # Create presigned URL
                            presigned_url = s3_handler.create_presigned_url(
                                bucket_name=BUCKET_NAME,
                                object_name=file_name,
                                expiration=60 * 5,  # 5 minutes
                                content_type=content_type
                            )
                            # Attach to payload
                            item.payload["presigned_url"] = presigned_url

                    all_results.extend(result)

                except Exception as e:
                    print(e)
            else:
                return ResponseModel(message=f"The collection {collection} is not found in the vector DB")

        # Sort results by score (descending)
        all_results.sort(key=lambda x: x.score, reverse=True)

        # Slice to top_n_total
        top_results = all_results[: req.top_n_total]

        # If user has asked for "text", "blog", or "ppt", we feed the chunk data into simple_gpt
        generated_text = None
        content_type_for_output = None

#         if req.types in ["text", "blog", "ppt"]:
#             # Gather textual chunks from the results, if they exist
#             chunk_data = []
#             for item in top_results:
#                 if "text" in item.payload:
#                     chunk_data.append(item.payload["text"])

#             # Combine all chunk text into one user prompt (adjust as needed)
#             user_prompt = "Question: "+req.query+"Available context : "+"\n".join(chunk_data)
#             system_prompt = "Answer the question based on the available context for the question given, strictly in a json format for a" +req.types +"""
# If Blog then json has to be definetly like :
# {"title":"Some title from context/question","Subheading1":"Some subheading from context/question","Content1":"Some content from context/question","Subheading1":"Some subheading from context/question","Content1":"Some content from context/question"}
# If ppt then json has to be definetly like :
# {"title":"Some title from context/question","Subheading1":"Some subheading from context/question","Content1":"Some content from context/question","Subheading1":"Some subheading from context/question","Content1":"Some content from context/question"}
# Always make sure to return just the json , no need to add even markdown or anything, just plain json text, the sub heading has to be suffiently big as per the content or as per the user specification.
# Always follow, subheading-content, subheading-content format
# """
#             # Example: call simple_gpt
#             generated_text = simple_gpt(
#                 user_prompt=user_prompt,
#                 system_prompt=system_prompt,
#                   model="gpt-4o"  # or whichever model you prefer
#             )

#             # Decide how to label the content in your response
#             # e.g. "content": "blog" or "text" or "ppt"
#             content_type_for_output = req.types

#         # Build the response
#         response_dict = {
#             "status": "success",
#             "results": top_results  # your original search results
#         }

#         # If we generated text, include it in the JSON
#         if generated_text and content_type_for_output:
#             response_dict["generated_content"] = {
#                 "content": content_type_for_output,
#                 "text": eval(generated_text)
#             }
        response_dict = {
                "status": "success",
                "result_chunks": top_results
            }
        if req.types in ["text", "blog", "ppt", "image","pdf"]:
            chunk_data = [item.payload["chunk_text"] for item in top_results if "chunk_text" in item.payload]
            print(chunk_data)

            generated_text = None
            if req.types == "text":
                generated_text = generate_text_content(req.query, chunk_data)
            elif req.types == "blog":
                generated_text = generate_blog_content(req.query, chunk_data)
            elif req.types == "ppt":
                generated_text = generate_ppt_content(req.query, chunk_data)
            elif req.types == "pdf":
                generated_text = generate_blog_content(req.query, chunk_data)
            elif req.types == "image":
                return response_dict
            response_dict={}
            content_type_for_output = req.types
            print(generated_text)
            generated_text = generated_text.replace("```json","").replace("```","")
            if generated_text and content_type_for_output:
                response_dict["generated_content"] = {
                    "content": content_type_for_output,
                    "text": eval(generated_text)
                }


        return response_dict

    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Generation failed")
    

@app.post("/data/ppt", tags=["PPT"])
def train(presentation_data :dict , db: Session = Depends(get_db),token: str = Depends(verify_token)):
    try:
        link = create_and_share_presentation(presentation_data)
        print("✅ Public Google Slides link:", link)
        return ResponseModel(message="Google sildes generation complete .",payload={"link":link})#{"status": "success", "message": "Training complete."}   
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="PPT creation failed")
    
@app.post("/data/pdf", tags=["PDF"])
def train(docx_data :dict , db: Session = Depends(get_db),token: str = Depends(verify_token)):
    try:
        link = create_and_share_document(docx_data)
        print("✅ Public Google doc link:", link)
        return ResponseModel(message="Google doc generation complete .",payload={"link":link})#{"status": "success", "message": "Training complete."}   
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="PDF creation failed")