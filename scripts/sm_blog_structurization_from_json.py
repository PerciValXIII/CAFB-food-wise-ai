"""
================================================================================
Script Name: sm_blog_structurization_from_jsonl.py
Author: Swattik Maiti
Description:
    This script reads blog post data from a JSONL file located at:
        mainfolder/data/text/blog_posts.jsonl

    Each line in the JSONL file is a blog post object containing:
        - title
        - url
        - date
        - content (text body of the blog)
        - image_filenames
        - image_links

    The script:
    - Parses each blog post
    - Assigns a unique file_id of the form 'blo_001', 'blo_002', ...
    - Stores structured rows in a CSV file with the following columns:
        - file_id       (unique ID per blog post)
        - file_name     (from 'title')
        - date          (from 'date')
        - url           (from 'url')
        - content       (plain blog text, not JSON)

    Output is saved to:
        mainfolder/data/parsed_blog_posts.csv

Dependencies:
    - pandas
================================================================================
"""

import os
import json
import pandas as pd


if __name__ == "__main__":
    # Define paths
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_jsonl = os.path.join(root_dir, "data", "text", "blog_posts.jsonl")
    output_csv = os.path.join(root_dir, "data", "supabase_structured_data", "parsed_blog_posts.csv")

    rows = []

    with open(input_jsonl, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            try:
                blog_data = json.loads(line)
                file_id = f"blo_{idx:03d}"
                file_name = blog_data.get("title", "")
                date = blog_data.get("date", "")
                url = blog_data.get("url", "")
                content = blog_data.get("content", "").strip()

                rows.append({
                    "file_id": file_id,
                    "file_name": file_name,
                    "date": date,
                    "url": url,
                    "content": content
                })

            except json.JSONDecodeError as e:
                print(f"Skipping line {idx}: JSON decode error - {e}")

    # Write to CSV
    df = pd.DataFrame(rows)
    df.to_csv(output_csv, index=False)
    print(f"Parsed {len(rows)} blog posts. Data saved to: {output_csv}")
