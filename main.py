from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import router
import uvicorn
import os
from mangum import Mangum
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create FastAPI app instance
app = FastAPI()
handler = Mangum(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router.app)


# Define server running function
def run_server():
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)

# Entry point
if __name__ == "__main__":
    run_server()
