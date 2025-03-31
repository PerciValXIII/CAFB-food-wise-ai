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

