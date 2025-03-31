import logging
import json
from datetime import datetime,timedelta
import traceback
import os

# Ensure the logs directory exists
os.makedirs('logs', exist_ok=True)

# Configure Logging
logging.basicConfig(
    filename='logs/initial.logs',
    level=logging.INFO,
    format='%(message)s'
)

# Unified Logging Function
# def log_api_event(endpoint: str, method: str, status_code: int, request_body: dict, response_body: dict, error: str = None):
    
#     log_entry = {
#         "timestamp": (datetime.utcnow()+timedelta(hours=5, minutes=30)).isoformat() + "Z",
#         "endpoint": endpoint,
#         "method": method,
#         "status_code": status_code,
#         "request_body": request_body,
#         "response_body": response_body,
#         "error": error
#     }
#     log_entry.pop("response_body")
#     #logging.info(json.dumps(log_entry))
#     logging.info(log_entry)

