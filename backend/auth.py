from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
security = HTTPBearer()
import os

STATIC_BEARER_TOKEN = os.getenv("STATIC_BEARER_TOKEN")

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != STATIC_BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return credentials.credentials
