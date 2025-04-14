import os
import json
import pandas as pd
import fitz  # PyMuPDF
from dotenv import load_dotenv
import boto3
from supabase import create_client, Client

#loading env variables
load_dotenv()

# Supabase client setup
SUPABASE_URL = os.getenv("SUPABASE_URL") 
#service role secret key (not anon public)
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  
TABLE_NAME = "pdf_data"
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_default_region = os.getenv("AWS_DEFAULT_REGION")
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdf_dir = os.path.join(root_dir, "data", "sources", "collateral")
output_csv = os.path.join(root_dir, "data", "supabase_structured_data", "extracted_ppts", "parsed_collaterals.csv")
bucket_name = "cfab"
s3_folder = "on_premise_data/collateral/"
log_file = os.path.join(root_dir, "uploaded_files.txt")

#Initializing Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

#s3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name='us-east-1'  
)

#uploading user files to s3
for filename in os.listdir(pdf_dir):
    local_path = os.path.join(pdf_dir, filename)
    
    if os.path.isfile(local_path):
        s3_path = os.path.join(s3_folder, filename).replace("\\", "/")  
        print(f"Uploading {filename} to s3://{bucket_name}/{s3_path}")
        
        s3.upload_file(local_path, bucket_name, s3_path)

print("Upload complete!")

#checking supabase table records
response = supabase.table(TABLE_NAME).select("file_name").execute()
supabase_file_names = {entry["file_name"] for entry in response.data}
print(f"Files currently in Supabase: {len(supabase_file_names)}")

pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
new_files = [f for f in pdf_files if f not in supabase_file_names]
print(f"Files to process: {new_files}")
print(f"Found {len(new_files)} new PDF file(s) to process and upload.")

#file_id
all_file_ids = supabase.table(TABLE_NAME).select("file_id").execute()
existing_ids = [int(entry["file_id"].split("_")[1]) for entry in all_file_ids.data if "file_id" in entry]
starting_index = max(existing_ids) + 1 if existing_ids else 1
print(f"Starting from file_id: pdf_{starting_index:03d}")

class CollateralPDFParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.file_name = os.path.basename(pdf_path)
        self.file_type = "collateral"

    def parse_pdf(self, file_id):
        
        content_blocks = []

        doc = fitz.open(self.pdf_path)
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")  # Extract full page text
            if not text.strip():
                continue

            # Split on double newlines or paragraph-like blocks
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            for para_num, para_text in enumerate(paragraphs, start=1):
                clean_text = para_text.replace("\u00a0", " ")
                content_blocks.append({
                    "page": page_num,
                    "paragraph": para_num,
                    "text": clean_text
                })

        content_json = {
            "file_id": file_id,
            "filename": self.file_name,
            "content": content_blocks
        }
        
        return {
            "file_id": file_id,
            "file_name": self.file_name,
            "content_json": json.dumps(content_json),
            "file_type": self.file_type,
            "train": False
        }


for i, pdf_file in enumerate(sorted(new_files), start=starting_index):
    file_id = f"ppt_{i:03d}"
    pdf_path = os.path.join(pdf_dir, pdf_file)
    print(f"Processing {pdf_file} as {file_id}...")

    parser = CollateralPDFParser(pdf_path)
    parsed_data = parser.parse_pdf(file_id)

    if parsed_data:
        try:
            response = supabase.table(TABLE_NAME).insert(parsed_data).execute()
            print(f"Uploaded {pdf_file}: {response}")

            # Log it locally if needed
            with open(log_file, "a") as f:
                f.write(pdf_file + "\n")
        except Exception as e:
            print(f"Error uploading {pdf_file}: {e}")
    else:
        print(f"No data extracted from {pdf_file}. Skipping.")

print("All files processed.")