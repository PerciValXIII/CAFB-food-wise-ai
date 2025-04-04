import os
import json
from pathlib import Path
from collections import defaultdict

# Define common file type categories
TEXT_EXTENSIONS = {".jsonl", ".txt", ".csv", ".md"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".avi", ".mov"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg"}
PRESENTATION_EXTENSIONS = {".pptx", ".ppt"}
OTHER_EXTENSIONS = set()

def categorize_file(extension):
    """Categorize file type based on its extension."""
    if extension in TEXT_EXTENSIONS:
        return "text"
    elif extension in VIDEO_EXTENSIONS:
        return "video"
    elif extension in IMAGE_EXTENSIONS:
        return "image"
    elif extension in PRESENTATION_EXTENSIONS:
        return "presentation"
    else:
        OTHER_EXTENSIONS.add(extension)
        return "other"

def count_jsonl_entries(file_path):
    """Count the number of text entries inside a JSONL file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception as e:
        print(f"[ERROR] Could not count entries in {file_path}: {e}")
        return 0

def collect_metadata():
    """Scans one folder up, collects metadata on all files, and saves reports."""

    # Determine the parent directory
    parent_dir = Path(__file__).resolve().parent.parent
    metadata_list = []
    jsonl_entry_counts = {}

    file_type_counts = defaultdict(int)
    category_counts = defaultdict(int)
    dir_file_counts = defaultdict(lambda: defaultdict(int))
    total_files = 0

    text_entry_count = 0
    video_file_count = 0
    image_file_count = 0

    text_folder_entries = 0  # Total text entries found in JSONL files in 'text' folder

    print(f"[INFO] Scanning directory: {parent_dir}")

    # Traverse all files and subdirectories
    for file_path in parent_dir.rglob("*"):
        if file_path.is_file():
            file_extension = file_path.suffix.lower()
            file_category = categorize_file(file_extension)

            # Count file types and categories
            file_type_counts[file_extension] += 1
            category_counts[file_category] += 1
            dir_file_counts[file_path.parent][file_category] += 1
            total_files += 1

            # If it's a JSONL file, count its entries
            if file_extension == ".jsonl":
                num_records = count_jsonl_entries(file_path)
                jsonl_entry_counts[file_path.name] = num_records
                text_entry_count += num_records  # Total text entries

                # Check if it's inside the 'text' folder
                if "text" in file_path.parts:
                    text_folder_entries += num_records

                file_info = {
                    "file_name": file_path.name,
                    "absolute_path": str(file_path.resolve()),
                    "size_bytes": file_path.stat().st_size,
                    "last_modified": file_path.stat().st_mtime,
                    "num_records": num_records,
                    "containing_folder": str(file_path.parent)
                }
                metadata_list.append(file_info)
                print(f"[INFO] Collected metadata for {file_path.name}")

            elif file_category == "video":
                video_file_count += 1

            elif file_category == "image":
                image_file_count += 1

    # Create dataset overview
    dataset_overview = {
        "total_files": total_files,
        "file_type_distribution": dict(file_type_counts),
        "high_level_category_counts": dict(category_counts),
        "text_entries_in_jsonl": text_entry_count,
        "text_entries_in_text_folder": text_folder_entries,
        "videos_in_videos_folder": video_file_count,
        "images_in_images_folder": image_file_count,
        "directories": {str(dir_path): dict(file_counts) for dir_path, file_counts in dir_file_counts.items()},
        "jsonl_entry_counts": jsonl_entry_counts,
        "unrecognized_extensions": list(OTHER_EXTENSIONS)
    }

    # Save metadata to JSON
    output_dir = Path(__file__).resolve().parent
    metadata_file = output_dir / "metadata_summary.json"
    summary_file = output_dir / "dataset_summary.txt"

    with open(metadata_file, "w", encoding="utf-8") as json_file:
        json.dump({"dataset_overview": dataset_overview, "jsonl_files": metadata_list}, json_file, indent=4, ensure_ascii=False)

    # Generate a human-readable summary
    with open(summary_file, "w", encoding="utf-8") as txt_file:
        txt_file.write(f"Dataset Overview\n")
        txt_file.write(f"-----------------------------\n")
        txt_file.write(f"Total Files: {total_files}\n\n")

        txt_file.write(f"High-Level Breakdown:\n")
        txt_file.write(f"- Text Entries (From JSONL in 'text' folder): {text_folder_entries}\n")
        txt_file.write(f"- Videos in 'videos' folder: {video_file_count}\n")
        txt_file.write(f"- Images in 'images' folder: {image_file_count}\n\n")

        txt_file.write(f"File Type Distribution:\n")
        for ext, count in file_type_counts.items():
            txt_file.write(f"- {ext}: {count}\n")
        txt_file.write("\n")

        txt_file.write(f"High-Level Category Counts:\n")
        txt_file.write(f"- Text Files: {category_counts['text']}\n")
        txt_file.write(f"- Video Files: {category_counts['video']}\n")
        txt_file.write(f"- Image Files: {category_counts['image']}\n")
        txt_file.write(f"- Presentation Files: {category_counts['presentation']}\n")
        txt_file.write(f"- Other Files: {category_counts['other']}\n\n")

        txt_file.write(f"JSONL File Entry Counts (Total Text Entries: {text_entry_count}):\n")
        for jsonl_file, num_entries in jsonl_entry_counts.items():
            txt_file.write(f"- {jsonl_file}: {num_entries} entries\n")

        txt_file.write("\n")

        txt_file.write(f"Folder Breakdown:\n")
        for dir_path, file_counts in dir_file_counts.items():
            txt_file.write(f"- {dir_path}:\n")
            for category, count in file_counts.items():
                txt_file.write(f"  - {category}: {count}\n")
            txt_file.write("\n")

    print(f"[INFO] Metadata summary saved to {metadata_file}")
    print(f"[INFO] Dataset summary saved to {summary_file}")

if __name__ == "__main__":
    collect_metadata()
