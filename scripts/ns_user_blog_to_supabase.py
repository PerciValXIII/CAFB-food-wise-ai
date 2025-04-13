import os
import json
import pandas as pd
from supabase import create_client, Client

# Supabase Setup (Optional - use only if uploading to Supabase)
SUPABASE_URL = "https://pogfmrabqzbgtkctmyoo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBvZ2ZtcmFicXpiZ3RrY3RteW9vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MzM4OTU5OSwiZXhwIjoyMDU4OTY1NTk5fQ.DX-g2m0Oa02KTPOKVKHaNLFSgMzl4hYjvP1sdvSV1XQ"
TABLE_NAME = "blog_data"

# Directory paths
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
input_jsonl = os.path.join(root_dir, "data", "text", "blog_posts.jsonl")
output_csv = os.path.join(root_dir, "data", "supabase_structured_data", "extracted_ppts", "parsed_blog_posts.csv")
log_file = os.path.join(root_dir, "uploaded_files.txt")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch already uploaded blog post titles
response = supabase.table(TABLE_NAME).select("file_name").execute()
supabase_file_names = {entry["file_name"] for entry in response.data}
print(f"Blog posts already in Supabase: {len(supabase_file_names)}")

rows = []
new_files = []

# Parse blog posts
with open(log_file, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, start=1):
        try:
            blog_data = json.loads(line)
            title = blog_data.get("title", "").strip()

            if title in supabase_file_names:
                print(f"Skipping already uploaded post: {title}")
                continue

            file_id = f"blo_{idx:03d}"
            date = blog_data.get("date", "")
            url = blog_data.get("url", "")
            content = blog_data.get("content", "").strip()

            row = {
                "file_id": file_id,
                "file_name": title,
                "date": date,
                "url": url,
                "content": content
            }
            rows.append(row)
            new_files.append((file_id, title, row))

        except json.JSONDecodeError as e:
            print(f"Skipping line {idx}: JSON decode error - {e}")

# Save to CSV
df = pd.DataFrame(rows)
df.to_csv(output_csv, index=False)
print(f"Parsed {len(rows)} blog posts. Data saved to: {output_csv}")

# Optional Supabase upload
for file_id, title, row in new_files:
    try:
        insert_data = {
            "file_id": row["file_id"],
            "file_name": row["file_name"],
            "date": row["date"],
            "url": row["url"],
            "content": row["content"],
            "file_type": "blog",
            "train": False
        }
        response = supabase.table(TABLE_NAME).insert(insert_data).execute()
        print(f"Uploaded blog post: {title}")

        with open(input_jsonl, "a", encoding="utf-8") as log:
            log.write(f"{title}\n")

    except Exception as e:
        print(f"Error uploading blog post '{title}': {e}")
