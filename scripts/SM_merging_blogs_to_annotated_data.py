import os
import pandas as pd

def merge_blogposts_with_annotations(
    blog_jsonl_path="../data/text/blog_posts.jsonl",
    annotation_csv_path="../data/annotated_data/text_content_annotation.csv"
):
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Paths
    blog_path = os.path.join(base_dir, blog_jsonl_path)
    csv_path = os.path.join(base_dir, annotation_csv_path)
    xlsx_path = csv_path.replace(".csv", ".xlsx")

    # Load existing annotation CSV
    annotation_df = pd.read_csv(csv_path)

    # Load blog JSONL
    blog_df = pd.read_json(blog_path, lines=True)

    # Transform blog data to match annotation format
    transformed_blog_df = pd.DataFrame({
        'Source_file_ID': [f"blo_{i:03d}" for i in range(1, len(blog_df) + 1)],
        'File Name': blog_df['title'],
        'Source Type': 'blog',
        'Content': blog_df['content'].apply(lambda x: x.replace("\n", " <|endoftext|> ").strip()),
        'file type': 'link',
        'Filepath': ''
    })

    # Merge the DataFrames
    combined_df = pd.concat([annotation_df, transformed_blog_df], ignore_index=True)

    # Save updated files
    combined_df.to_csv(csv_path, index=False)
    combined_df.to_excel(xlsx_path, index=False)

    print("Blog posts merged with main annotation files (CSV & XLSX).")

# Optional: run directly
if __name__ == "__main__":
    merge_blogposts_with_annotations()
