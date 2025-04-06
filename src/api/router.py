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

        # Step 2: Search in each collection and gather top results
        all_results = []
        for collection in req.collections:
            if collection in ["ppt","pdf","blog","image"]:
                try:
                    result = qdrant_client.search(
                        collection_name=collection,
                        query_vector=embedding,
                        limit=req.top_n_each
                    )
                    all_results.extend(result)
                except Exception as e:
                    print(e)
            else:
                return ResponseModel(message=f"The collection {collection} is not found in the vector DB")
        all_results.sort(key=lambda x: x.score, reverse=True)
        return {"status": "success", "results": all_results[:req.top_n_total]}

    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Similarity search failed.")

