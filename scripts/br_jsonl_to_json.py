import json
import os
import argparse

def convert_jsonl_to_json(jsonl_files):
    """Convert each JSONL file in the list to a JSON file."""
    for jsonl_file in jsonl_files:
        if not os.path.exists(jsonl_file):
            print(f"[ERROR] File not found: {jsonl_file}")
            continue

        output_json_file = jsonl_file.replace(".jsonl", ".json")

        print(f"[INFO] Converting {jsonl_file} to {output_json_file}...")

        try:
            with open(jsonl_file, "r", encoding="utf-8") as infile:
                data = [json.loads(line) for line in infile if line.strip()]

            with open(output_json_file, "w", encoding="utf-8") as outfile:
                json.dump(data, outfile, indent=4, ensure_ascii=False)

            print(f"[INFO] Successfully created {output_json_file}")

        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse {jsonl_file}: {e}")
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert JSONL files to JSON format.")
    parser.add_argument("jsonl_files", nargs="+", help="List of JSONL file paths to convert.")
    
    args = parser.parse_args()
    
    convert_jsonl_to_json(args.jsonl_files)
